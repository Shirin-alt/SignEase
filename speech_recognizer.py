import whisper
import numpy as np
import io
import tempfile
import os
import threading
import time
import subprocess
from collections import Counter
import re

class WhisperSpeechRecognizer:
    """Speech recognition using OpenAI Whisper with support for Taglish and multiple languages"""

    def __init__(self, model_size="base"):
        """
        Initialize Whisper model
        model_size: "tiny", "base", "small", "medium", "large"
        Larger models are more accurate but slower
        """
        self.model_size = model_size
        self.model = None
        self._lock = threading.Lock()
        self._load_model()
        
        # Common Tagalog words for language detection
        self.tagalog_words = {
            'ang', 'sa', 'ng', 'kayo', 'kami', 'tayo', 'sila', 'ako', 'ikaw', 'siya',
            'ito', 'yan', 'yun', 'dito', 'doon', 'dyan', 'nito', 'noon', 'nyan',
            'ano', 'sino', 'saan', 'kailan', 'bakit', 'paano', 'ilang',
            'mabuti', 'masama', 'malaki', 'maliit', 'mainit', 'malamig',
            'umiibik', 'kumakain', 'natutulog', 'naglalaro', 'nagsasalita',
            'oo', 'hindi', 'ayaw', 'gusto', 'dapat', 'maaari', 'pwede',
            'salamat', 'merong', 'walang', 'may', 'wala', 'puro', 'lahat',
            'isa', 'dalawa', 'tatlo', 'apat', 'lima', 'anim', 'pito', 'walo', 'siyam', 'sampu'
        }

    def _load_model(self):
        """Load the Whisper model"""
        try:
            print(f"[Whisper] Loading {self.model_size} model...")
            self.model = whisper.load_model(self.model_size)
            print(f"[Whisper] Model loaded successfully")
        except Exception as e:
            print(f"[Whisper] Error loading model: {e}")
            self.model = None

    def _detect_tagalog_ratio(self, text):
        """Detect the ratio of Tagalog words in the text"""
        words = re.findall(r'\b\w+\b', text.lower())
        if not words:
            return 0.0
        
        tagalog_count = sum(1 for word in words if word in self.tagalog_words)
        return tagalog_count / len(words)

    def _improve_taglish_accuracy(self, text, language):
        """Apply post-processing improvements for Taglish"""
        # Common Taglish replacements and corrections
        replacements = {
            r'\byung\b': 'yung',
            r'\bkung\b': 'kung',
            r'\bkasi\b': 'kasi',
            r'\byun\b': 'yun',
            r'\bdyan\b': 'dyan',
            r'\bdito\b': 'dito',
            r'\bdoon\b': 'doon',
        }
        
        result = text
        for pattern, replacement in replacements.items():
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        
        return result.strip()

    def transcribe_audio(self, audio_data, language=None):
        """
        Transcribe audio data to text - English and Tagalog only for better accuracy
        audio_data: bytes or numpy array
        language: 'en' for English, 'tl' for Tagalog, or None for auto-detect between these two
        Returns: dict with text, language, and confidence
        """
        if self.model is None:
            return {"text": "", "error": "Model not loaded"}

        try:
            with self._lock:
                # Convert audio to WAV format for better compatibility
                audio_path = self._convert_audio_to_wav(audio_data)
                
                if audio_path is None:
                    return {"text": "", "error": "Failed to process audio"}
                
                try:
                    # If no language specified, try both English and Tagalog and pick the most confident
                    if language is None:
                        print("[Whisper] Transcribing with English...")
                        # Try English first
                        en_result = self.model.transcribe(
                            audio_path,
                            language='en',
                            fp16=False,
                            temperature=0.0,
                            best_of=5,
                            beam_size=5
                        )
                        
                        print("[Whisper] Transcribing with Tagalog...")
                        # Try Tagalog
                        tl_result = self.model.transcribe(
                            audio_path,
                            language='tl',
                            fp16=False,
                            temperature=0.0,
                            best_of=5,
                            beam_size=5
                        )
                        
                        # Use English result by default (it's more reliable)
                        # But if both have similar confidence, prefer the one with more text
                        en_conf = en_result.get("confidence", 1.0)
                        tl_conf = tl_result.get("confidence", 1.0)
                        en_text = en_result["text"].strip()
                        tl_text = tl_result["text"].strip()
                        
                        # If Tagalog has significantly better confidence, use it
                        if tl_conf > en_conf + 0.1 and len(tl_text) > 0:
                            print("[Whisper] Detected: Tagalog")
                            transcription_result = tl_result
                            detected_language = 'tl'
                        else:
                            print("[Whisper] Detected: English")
                            transcription_result = en_result
                            detected_language = 'en'
                    else:
                        # Use specified language (restrict to 'en' or 'tl')
                        if language not in ['en', 'tl']:
                            language = 'en'  # Default to English if invalid
                        
                        print(f"[Whisper] Using specified language: {language}")
                        transcription_result = self.model.transcribe(
                            audio_path,
                            language=language,
                            fp16=False,
                            temperature=0.0,
                            best_of=5,
                            beam_size=5
                        )
                        detected_language = language
                    
                    text = transcription_result["text"].strip()
                    
                    # Clean up text for Tagalog
                    if detected_language == 'tl':
                        text = self._improve_taglish_accuracy(text, 'tl')
                    
                    return {
                        "text": text,
                        "language": detected_language,
                        "confidence": transcription_result.get("confidence", 1.0)
                    }
                finally:
                    # Clean up
                    if os.path.exists(audio_path):
                        try:
                            os.unlink(audio_path)
                        except:
                            pass

        except Exception as e:
            print(f"[Whisper] Transcription error: {e}")
            return {"text": "", "error": str(e)}

    def _convert_audio_to_wav(self, audio_data):
        """Convert audio data to WAV format using FFmpeg"""
        # Try different extensions based on common formats
        for ext in ['.webm', '.ogg', '.mp4', '.wav', '.m4a']:
            input_path = None
            output_path = None
            try:
                with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as temp_file:
                    temp_file.write(audio_data)
                    input_path = temp_file.name

                output_path = input_path.replace(ext, '_converted.wav')

                # Use FFmpeg to convert audio to WAV format
                result = subprocess.run([
                    'ffmpeg', '-y', '-i', input_path, '-acodec', 'pcm_s16le',
                    '-ar', '16000', '-ac', '1', output_path
                ], capture_output=True, text=True, timeout=30)

                if result.returncode == 0 and os.path.exists(output_path):
                    print(f"[FFmpeg] Successfully converted from {ext}")
                    # Delete input file but return output path
                    if input_path and os.path.exists(input_path):
                        try:
                            os.unlink(input_path)
                        except:
                            pass
                    return output_path
                else:
                    print(f"[FFmpeg] Conversion failed for {ext}")
            except subprocess.TimeoutExpired:
                print(f"[FFmpeg] Timeout converting {ext}")
            except Exception as conv_error:
                print(f"[FFmpeg] Error converting {ext}: {conv_error}")
            finally:
                # Clean up input file if it still exists
                if input_path and os.path.exists(input_path):
                    try:
                        os.unlink(input_path)
                    except:
                        pass
        
        # If all conversions failed, return None
        print("[Whisper] All audio conversions failed")
        return None

    def get_supported_languages(self):
        """Get list of supported languages"""
        return [
            "en", "zh", "de", "es", "ru", "ko", "fr", "ja", "pt", "tr", "pl", "ca", "nl",
            "ar", "sv", "it", "id", "hi", "fi", "vi", "he", "uk", "el", "ms", "cs", "ro",
            "da", "hu", "ta", "no", "th", "ur", "hr", "bg", "lt", "la", "mi", "ml", "cy",
            "sk", "te", "fa", "lv", "bn", "sr", "az", "sl", "kn", "et", "mk", "br", "eu",
            "is", "hy", "ne", "mn", "bs", "kk", "sq", "sw", "gl", "mr", "pa", "si", "km",
            "sn", "yo", "so", "af", "oc", "ka", "be", "tg", "sd", "gu", "am", "yi", "lo",
            "uz", "fo", "ht", "ps", "tk", "nn", "mt", "sa", "lb", "my", "bo", "tl", "mg",
            "as", "tt", "haw", "ln", "ha", "ba", "jw", "su"
        ]

# Global instance
whisper_recognizer = None

def get_whisper_recognizer():
    """Get or create global Whisper recognizer instance"""
    global whisper_recognizer
    if whisper_recognizer is None:
        whisper_recognizer = WhisperSpeechRecognizer()
    return whisper_recognizer

if __name__ == "__main__":
    # Test the recognizer
    recognizer = get_whisper_recognizer()
    print("Whisper speech recognizer initialized")
    print(f"Supported languages: {len(recognizer.get_supported_languages())} languages")
