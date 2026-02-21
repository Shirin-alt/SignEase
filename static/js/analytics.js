// Analytics System
const Analytics = {
    // Get analytics data
    getData() {
        const data = localStorage.getItem('signease_analytics');
        if (data) {
            return JSON.parse(data);
        }
        return {
            totalSigns: 0,
            correctSigns: 0,
            practiceTime: 0,
            dailyProgress: {},
            sessionStart: Date.now()
        };
    },

    // Save analytics data
    saveData(data) {
        localStorage.setItem('signease_analytics', JSON.stringify(data));
    },

    // Track sign detection
    trackSign(isCorrect) {
        const data = this.getData();
        data.totalSigns += 1;
        if (isCorrect) {
            data.correctSigns += 1;
        }
        
        const today = new Date().toDateString();
        if (!data.dailyProgress[today]) {
            data.dailyProgress[today] = 0;
        }
        data.dailyProgress[today] += 1;
        
        this.saveData(data);
        this.updateUI();
    },

    // Update practice time
    updatePracticeTime() {
        const data = this.getData();
        const elapsed = Math.floor((Date.now() - data.sessionStart) / 1000);
        data.practiceTime += elapsed;
        data.sessionStart = Date.now();
        this.saveData(data);
    },

    // Calculate accuracy
    getAccuracy() {
        const data = this.getData();
        if (data.totalSigns === 0) return 0;
        return Math.round((data.correctSigns / data.totalSigns) * 100);
    },

    // Format time
    formatTime(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        if (hours > 0) {
            return `${hours}h ${minutes}m`;
        }
        return `${minutes}m`;
    },

    // Get last 7 days data
    getLast7Days() {
        const data = this.getData();
        const days = [];
        const labels = [];
        
        for (let i = 6; i >= 0; i--) {
            const date = new Date(Date.now() - i * 86400000);
            const dateStr = date.toDateString();
            const count = data.dailyProgress[dateStr] || 0;
            
            days.push(count);
            labels.push(date.toLocaleDateString('en-US', { weekday: 'short' }));
        }
        
        return { days, labels };
    },

    // Draw bar chart
    drawChart() {
        const canvas = document.getElementById('progressChart');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        const { days, labels } = this.getLast7Days();
        
        const width = canvas.width;
        const height = canvas.height;
        const padding = 40;
        const barWidth = (width - padding * 2) / days.length;
        const maxValue = Math.max(...days, 10);
        
        ctx.clearRect(0, 0, width, height);
        
        // Draw bars
        days.forEach((value, index) => {
            const barHeight = (value / maxValue) * (height - padding * 2);
            const x = padding + index * barWidth + barWidth * 0.2;
            const y = height - padding - barHeight;
            
            const gradient = ctx.createLinearGradient(0, y, 0, height - padding);
            gradient.addColorStop(0, '#0052cc');
            gradient.addColorStop(1, '#4a90e2');
            
            ctx.fillStyle = gradient;
            ctx.fillRect(x, y, barWidth * 0.6, barHeight);
            
            // Draw value
            ctx.fillStyle = '#333';
            ctx.font = '12px Inter';
            ctx.textAlign = 'center';
            ctx.fillText(value, x + barWidth * 0.3, y - 5);
            
            // Draw label
            ctx.fillStyle = '#6c757d';
            ctx.fillText(labels[index], x + barWidth * 0.3, height - padding + 20);
        });
    },

    // Update UI
    updateUI() {
        const data = this.getData();
        const accuracy = this.getAccuracy();
        
        const totalEl = document.getElementById('totalSignsStat');
        const accuracyEl = document.getElementById('accuracyStat');
        const timeEl = document.getElementById('practiceTimeStat');
        
        if (totalEl) totalEl.textContent = data.totalSigns;
        if (accuracyEl) accuracyEl.textContent = accuracy + '%';
        if (timeEl) timeEl.textContent = this.formatTime(data.practiceTime);
        
        this.drawChart();
    },

    // Initialize
    init() {
        this.updateUI();
        setInterval(() => this.updatePracticeTime(), 60000); // Update every minute
    }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    Analytics.init();
});

// Export for use in other scripts
window.Analytics = Analytics;
