// Gamification System
const Gamification = {
    // Get data from localStorage
    getData() {
        const data = localStorage.getItem('signease_game');
        if (data) {
            return JSON.parse(data);
        }
        return {
            xp: 0,
            level: 1,
            streak: 0,
            lastVisit: new Date().toDateString()
        };
    },

    // Save data to localStorage
    saveData(data) {
        localStorage.setItem('signease_game', JSON.stringify(data));
    },

    // Calculate level from XP
    getLevel(xp) {
        return Math.floor(xp / 100) + 1;
    },

    // Calculate XP needed for next level
    getXPForNextLevel(level) {
        return level * 100;
    },

    // Calculate progress percentage
    getProgress(xp, level) {
        const currentLevelXP = (level - 1) * 100;
        const nextLevelXP = level * 100;
        const progress = ((xp - currentLevelXP) / (nextLevelXP - currentLevelXP)) * 100;
        return Math.min(Math.max(progress, 0), 100);
    },

    // Add XP
    addXP(amount) {
        const data = this.getData();
        data.xp += amount;
        const newLevel = this.getLevel(data.xp);
        
        if (newLevel > data.level) {
            data.level = newLevel;
            this.showLevelUp(newLevel);
        }
        
        this.saveData(data);
        this.updateUI();
    },

    // Update streak
    updateStreak() {
        const data = this.getData();
        const today = new Date().toDateString();
        const yesterday = new Date(Date.now() - 86400000).toDateString();
        
        if (data.lastVisit === yesterday) {
            data.streak += 1;
        } else if (data.lastVisit !== today) {
            data.streak = 1;
        }
        
        data.lastVisit = today;
        this.saveData(data);
        this.updateUI();
    },

    // Show level up notification
    showLevelUp(level) {
        // Removed level up popup
    },

    // Update UI elements
    updateUI() {
        const data = this.getData();
        const progress = this.getProgress(data.xp, data.level);
        
        document.getElementById('streakCount').textContent = data.streak;
        document.getElementById('xpCount').textContent = data.xp + ' XP';
        document.getElementById('levelBadge').textContent = 'Lvl ' + data.level;
        document.getElementById('xpProgressBar').style.width = progress + '%';
        
        if (typeof renderRewards === 'function') {
            renderRewards();
        }
    },

    // Sync to server
    async syncToServer() {
        const data = this.getData();
        try {
            await fetch('/sync_progress', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({xp: data.xp, level: data.level, streak: data.streak})
            });
        } catch (e) {
            console.error('Sync failed:', e);
        }
    },

    // Initialize
    init() {
        this.updateStreak();
        this.updateUI();
        setInterval(() => this.syncToServer(), 30000);
    }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    Gamification.init();
});

// Export for use in other scripts
window.Gamification = Gamification;
