// Main JavaScript for Sign Detector

// Global variables
let sessionStartTime = Date.now();
let detectionCount = 0;
let signCounts = {};
let lastSavedSign = null;
let lastSavedTime = 0;

// Speech recognition variables
let recognition = null;
let isRecording = false;
let speechText = '';
let userPreference = window.userPreference || 'sign_detection';
let mediaRecorder = null;
let audioChunks = [];

// Update session time display
function updateSessionTime() {
    const elapsed = Math.floor((Date.now() - sessionStartTime) / 1000);
    const minutes = Math.floor(elapsed / 60);
    const seconds = elapsed % 60;
    const timeString = `${minutes}:${seconds.toString().padStart(2, '0')}`;
    document.getElementById('session-time').textContent = timeString;
}

// Save detection to database
async function saveDetection(sign, confidence) {
    try {
        const response = await fetch('/save_detection', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                sign: sign,
                confidence: confidence
            })
        });
        const result = await response.json();
        if (result.status === 'saved') {
            console.log('Detection saved:', sign, confidence);
        }
    } catch (error) {
        console.error('Error saving detection:', error);
    }
}

// Fetch today's history
async function fetchTodayHistory() {
    try {
        const response = await fetch('/history_data');
        const data = await response.json();

        detectionCount = data.total_today || 0;
        document.getElementById('today-detections').textContent = detectionCount;

        // Update sign counts for most common sign
        signCounts = {};
        data.history.forEach(detection => {
            signCounts[detection.sign] = (signCounts[detection.sign] || 0) + 1;
        });

        const mostCommon = Object.keys(signCounts).reduce((a, b) =>
            signCounts[a] > signCounts[b] ? a : b, '-');
        document.getElementById('most-common-sign').textContent = mostCommon;

    } catch (error) {
        console.error('Error fetching today\'s history:', error);
    }
}

// Fetch latest detection from server
async function fetchLatestDetection() {
    try {
        const response = await fetch('/latest');
        const data = await response.json();

        const latestDetectionEl = document.getElementById('latest-detection');

        if (data.sign) {
            // Update detection display
            const confidence = Math.round(data.conf * 100);
            const filipinoText = data.filipino && data.filipino !== data.sign ? `<small class="text-info">${data.filipino}</small>` : '';
            latestDetectionEl.innerHTML = `
                <i class="fas fa-hand-paper fa-3x text-primary"></i>
                <h4 class="mt-2">${data.sign}</h4>
                ${filipinoText}
                <p class="text-muted">${confidence}% confidence</p>
            `;

            // Save detection if it's different from last saved or enough time has passed
            const currentTime = Date.now();
            if (data.sign !== lastSavedSign || (currentTime - lastSavedTime) > 5000) { // Save every 5 seconds max
                await saveDetection(data.sign, data.conf);
                lastSavedSign = data.sign;
                lastSavedTime = currentTime;

                // Refresh today's history after saving
                setTimeout(fetchTodayHistory, 1000);
            }
        } else {
            // No detection
            latestDetectionEl.innerHTML = `
                <i class="fas fa-hand-paper fa-3x text-muted"></i>
                <p>Waiting for sign...</p>
            `;
        }
    } catch (error) {
        console.error('Error fetching latest detection:', error);
        document.getElementById('latest-detection').innerHTML = `
            <i class="fas fa-exclamation-triangle fa-3x text-warning"></i>
            <p>Error loading detection</p>
        `;
    }
}

// Initialize speech recognition
function initSpeechRecognition() {
    // Always use server-side Whisper for better accuracy and consistency
    recognition = null;  // Disable browser speech recognition
}

// Toggle speech recording
function toggleRecording() {
    if (isRecording) {
        stopRecording();
    } else {
        startRecording();
    }
}

function startRecording() {
    if (!isRecording) {
        startWhisperRecording();
    }
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
    }
}

// Fallback speech recognition using server-side Whisper
async function startWhisperRecording() {
    try {
        console.log('Requesting microphone access...');
        const stream = await navigator.mediaDevices.getUserMedia({
            audio: {
                sampleRate: 16000,
                channelCount: 1,
                echoCancellation: true,
                noiseSuppression: true
            }
        });
        console.log('Microphone access granted');

        // Try different MIME types for better compatibility
        let mimeType = 'audio/webm;codecs=opus';
        if (!MediaRecorder.isTypeSupported(mimeType)) {
            mimeType = 'audio/webm';
        }
        if (!MediaRecorder.isTypeSupported(mimeType)) {
            mimeType = 'audio/mp4';
        }
        if (!MediaRecorder.isTypeSupported(mimeType)) {
            mimeType = ''; // Let browser choose
        }

        console.log('Using MIME type:', mimeType);
        mediaRecorder = new MediaRecorder(stream, { mimeType: mimeType });
        audioChunks = [];

        mediaRecorder.ondataavailable = (event) => {
            console.log('Audio data available, size:', event.data.size);
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = async () => {
            console.log('Recording stopped, chunks:', audioChunks.length);
            isRecording = false;
            document.getElementById('speech-toggle').innerHTML = '<i class="fas fa-microphone"></i> Start Recording';
            document.getElementById('speech-toggle').classList.remove('btn-danger');
            document.getElementById('speech-toggle').classList.add('btn-primary');
            
            const audioBlob = new Blob(audioChunks, { type: mimeType || 'audio/webm' });
            console.log('Audio blob created, size:', audioBlob.size);
            
            stream.getTracks().forEach(track => track.stop());
            
            if (audioBlob.size > 0) {
                await sendAudioToServer(audioBlob);
            } else {
                document.getElementById('speech-text').innerHTML = '<span class="text-muted">No audio recorded</span>';
            }
        };

        mediaRecorder.onerror = (event) => {
            console.error('MediaRecorder error:', event.error);
            document.getElementById('speech-text').innerHTML = 'Recording error: ' + event.error.message;
        };

        mediaRecorder.start();
        isRecording = true;
        document.getElementById('speech-toggle').innerHTML = '<i class="fas fa-stop"></i> Stop Recording';
        document.getElementById('speech-toggle').classList.remove('btn-primary');
        document.getElementById('speech-toggle').classList.add('btn-danger');
        document.getElementById('speech-text').classList.add('recording');
        document.getElementById('speech-text').innerHTML = '<span class="text-muted">Recording... Click Stop when done</span>';
    } catch (error) {
        console.error('Error accessing microphone:', error);
        document.getElementById('speech-text').innerHTML = 'Error accessing microphone: ' + error.message + '. Please check permissions.';
    }
}

async function sendAudioToServer(audioBlob) {
    const formData = new FormData();
    let filename = 'recording.webm';
    if (audioBlob.type.includes('mp4')) {
        filename = 'recording.mp4';
    } else if (audioBlob.type.includes('wav')) {
        filename = 'recording.wav';
    } else if (audioBlob.type.includes('ogg')) {
        filename = 'recording.ogg';
    }
    formData.append('audio', audioBlob, filename);

    try {
        document.getElementById('speech-text').innerHTML = '<span class="text-muted">Processing...</span>';

        const response = await fetch('/speech_recognize', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (response.ok) {
            speechText = result.text;
            document.getElementById('speech-text').innerHTML = speechText;
            document.getElementById('speech-text').classList.remove('recording');
            updateLatestTranscription(speechText);
            saveTranscription(speechText);
        } else {
            document.getElementById('speech-text').innerHTML = 'Error: ' + result.error;
        }
    } catch (error) {
        console.error('Error sending audio to server:', error);
        document.getElementById('speech-text').innerHTML = 'Error processing audio. Please try again.';
    }
}

// Update latest transcription display
function updateLatestTranscription(text) {
    const latestTranscriptionEl = document.getElementById('latest-transcription');
    if (text) {
        latestTranscriptionEl.innerHTML = `
            <i class="fas fa-comment-dots fa-3x text-success"></i>
            <h4 class="mt-2">${text}</h4>
            <p class="text-muted">Just now</p>
        `;
    } else {
        latestTranscriptionEl.innerHTML = `
            <i class="fas fa-comment-dots fa-3x text-muted"></i>
            <p>Waiting for speech...</p>
        `;
    }
}

// Save transcription to database
async function saveTranscription(text) {
    try {
        const response = await fetch('/save_transcription', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                text: text
            })
        });
        const result = await response.json();
        if (result.status === 'saved') {
            console.log('Transcription saved:', text);
        }
    } catch (error) {
        console.error('Error saving transcription:', error);
    }
}

// Check if detector is ready
async function checkDetectorReady() {
    try {
        const response = await fetch('/check_detector');
        const data = await response.json();
        return data.initialized === true;
    } catch (error) {
        console.error('Error checking detector status:', error);
        return false;
    }
}

// Hide loading overlay
function hideLoadingOverlay() {
    const loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay && loadingOverlay.style.display !== 'none') {
        console.log('[Dashboard] Hiding loading overlay');
        loadingOverlay.style.display = 'none';
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Handle loading overlay for sign detection
    const videoFeed = document.getElementById('video-feed');
    const loadingOverlay = document.getElementById('loading-overlay');
    
    if (videoFeed && loadingOverlay && userPreference === 'sign_detection') {
        videoFeed.addEventListener('load', function() {
            console.log('[Dashboard] Video feed loaded');
            hideLoadingOverlay();
        });
        
        setTimeout(function() {
            hideLoadingOverlay();
        }, 3000);
    }

    const speechToggleBtn = document.getElementById('speech-toggle');
    if (speechToggleBtn) {
        console.log('Setting up speech toggle button');
        speechToggleBtn.addEventListener('click', function(e) {
            console.log('Speech toggle button clicked, isRecording:', isRecording);
            toggleRecording();
        });
    }
    
    window.toggleRecording = toggleRecording;
});
