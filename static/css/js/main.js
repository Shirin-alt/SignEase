document.addEventListener('DOMContentLoaded', function() {
    // Sidebar Toggle
    const sidebarCollapse = document.getElementById('sidebarCollapse');
    if (sidebarCollapse) {
        sidebarCollapse.addEventListener('click', function() {
            document.getElementById('sidebar').classList.toggle('active');
        });
    }

    // Latest Detection Update
    function updateLatestDetection() {
        fetch('/latest')
            .then(response => response.json())
            .then(data => {
                const detectionBox = document.getElementById('latest-detection');
                if (detectionBox) {
                    if (data.sign) {
                        detectionBox.innerHTML = `<h2 class="display-4">${data.sign}</h2><p class="text-muted">Confidence: ${(data.conf * 100).toFixed(1)}%</p>`;
                    } else {
                        detectionBox.innerHTML = `<i class="fas fa-hand-paper fa-3x"></i><p>Waiting for sign...</p>`;
                    }
                }
            })
            .catch(error => console.error('Error fetching latest detection:', error));
    }

    // Session Timer
    let sessionSeconds = 0;
    setInterval(() => {
        sessionSeconds++;
        const sessionTimeElement = document.getElementById('session-time');
        if(sessionTimeElement) {
            const minutes = Math.floor(sessionSeconds / 60);
            const seconds = sessionSeconds % 60;
            sessionTimeElement.textContent = `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
        }
    }, 1000);

    // Run update functions only on the index page
    if (document.getElementById('video-feed')) {
        setInterval(updateLatestDetection, 1000);
    }

    // Handle Retrain Model button click
    const retrainBtn = document.getElementById('retrain-btn');
    if (retrainBtn) {
        retrainBtn.addEventListener('click', function(e) {
            e.preventDefault();
            if (confirm('Are you sure you want to retrain the model? This may take a while.')) {
                fetch('/retrain', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'started') {
                            alert('Model retraining started in the background.');
                        } else if (data.status === 'already_running') {
                            alert('Retraining is already in progress.');
                        }
                    });
            }
        });
    }
});