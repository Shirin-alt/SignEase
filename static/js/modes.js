// Mode Switcher
const ModeSwitcher = {
    currentMode: 'sign',
    detectionInterval: null,
    
    init() {
        const savedMode = localStorage.getItem('learningMode') || 'sign';
        this.switchMode(savedMode);
        
        document.querySelectorAll('.mode-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const mode = e.currentTarget.dataset.mode;
                this.switchMode(mode);
            });
        });
    },
    
    switchMode(mode) {
        this.currentMode = mode;
        localStorage.setItem('learningMode', mode);
        
        // Update button states
        document.querySelectorAll('.mode-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.mode === mode);
        });
        
        // Show/hide content
        document.getElementById('signMode').style.display = mode === 'sign' ? 'block' : 'none';
        document.getElementById('speechMode').style.display = mode === 'speech' ? 'block' : 'none';
        
        // Start/stop detection
        if (mode === 'sign') {
            this.startSignDetection();
        } else {
            this.stopSignDetection();
            this.initSpeechRecognition();
        }
    },
    
    startSignDetection() {
        if (this.detectionInterval) return;
        this.lastAddedSign = null;
        this.lastAddedTime = 0;
        this.transcriptSigns = new Set();
        
        this.detectionInterval = setInterval(async () => {
            try {
                const response = await fetch('/latest');
                const data = await response.json();
                
                const label = document.getElementById('detectionLabel');
                if (!label) return;
                
                const signName = label.querySelector('.sign-name');
                const confidence = label.querySelector('.confidence');
                
                if (data.sign && data.conf >= 0.75) {
                    const conf = Math.round(data.conf * 100);
                    signName.textContent = data.sign;
                    confidence.textContent = conf + '%';
                    label.classList.add('active');
                    
                    const now = Date.now();
                    if (conf >= 80 && !this.transcriptSigns.has(data.sign)) {
                        this.addToTranscript(data.sign, conf);
                        this.onCorrectDetection();
                        this.transcriptSigns.add(data.sign);
                        this.lastAddedSign = data.sign;
                        this.lastAddedTime = now;
                    }
                } else {
                    signName.textContent = 'No hand detected';
                    confidence.textContent = '0%';
                    label.classList.remove('active');
                }
            } catch (error) {
                console.error('Detection error:', error);
            }
        }, 300);
    },
    
    stopSignDetection() {
        if (this.detectionInterval) {
            clearInterval(this.detectionInterval);
            this.detectionInterval = null;
        }
    },
    
    onCorrectDetection() {
        if (window.Gamification) window.Gamification.addXP(10);
        if (window.Analytics) window.Analytics.trackSign(true);
    },
    
    addToTranscript(sign, confidence) {
        console.log('Adding to transcript:', sign, confidence);
        const transcriptList = document.getElementById('transcriptList');
        if (!transcriptList) {
            console.error('Transcript list not found');
            return;
        }
        
        const time = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        const entry = document.createElement('div');
        entry.style.cssText = 'padding: 0.75rem; margin-bottom: 0.5rem; background: var(--bg-color); border-radius: 8px; border-left: 3px solid #0052cc;';
        entry.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-weight: 600; color: var(--text-color);">${sign.toUpperCase()}</span>
                <span style="font-size: 0.85rem; color: var(--text-gray);">${confidence}%</span>
            </div>
            <div style="font-size: 0.8rem; color: var(--text-gray); margin-top: 0.25rem;">${time}</div>
        `;
        
        if (transcriptList.querySelector('p')) {
            transcriptList.innerHTML = '';
        }
        
        transcriptList.insertBefore(entry, transcriptList.firstChild);
        console.log('Entry added to transcript');
        
        if (transcriptList.children.length > 20) {
            transcriptList.removeChild(transcriptList.lastChild);
        }
        
        this.saveToDatabase(sign, confidence / 100);
    },
    
    async saveToDatabase(sign, confidence) {
        console.log('Saving to database:', sign, confidence);
        try {
            const response = await fetch('/save_detection', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({sign: sign, confidence: confidence})
            });
            const result = await response.json();
            console.log('Save result:', result);
        } catch (error) {
            console.error('Failed to save detection:', error);
        }
    },
    
    initSpeechRecognition() {
        const toggleBtn = document.getElementById('speech-toggle');
        if (!toggleBtn) return;
        
        toggleBtn.addEventListener('click', () => this.toggleSpeech());
    },
    
    toggleSpeech() {
        if (window.toggleRecording) {
            window.toggleRecording();
        }
    }
};

document.addEventListener('DOMContentLoaded', () => ModeSwitcher.init());

function clearTranscript() {
    const transcriptList = document.getElementById('transcriptList');
    if (transcriptList) {
        transcriptList.innerHTML = '<p style="color: var(--text-gray); font-style: italic;">Detected signs will appear here...</p>';
    }
    if (ModeSwitcher.transcriptSigns) {
        ModeSwitcher.transcriptSigns.clear();
    }
}
