/**
 * Achievements Page - Connected to App1.py Backend
 */

// State
let achievementsData = null;
let statsData = null;
let currentFilter = 'all';

// Initialize page
document.addEventListener('DOMContentLoaded', async () => {
    // Check authentication
    if (!api.isLoggedIn()) {
        window.location.href = 'login-page.html';
        return;
    }

    // Verify session is still valid
    try {
        await api.me();
    } catch (error) {
        console.error('Session validation failed:', error);
        localStorage.removeItem('autorevise_user');
        window.location.href = 'login-page.html';
        return;
    }

    await loadAchievementsData();
    await loadStatsData();
    setupEventListeners();
});

/**
 * Load achievements data from backend
 */
async function loadAchievementsData() {
    try {
        const response = await api.getAchievements();
        achievementsData = response;
        renderAchievements();
        updateAchievementStats();
    } catch (error) {
        console.error('Failed to load achievements:', error);
        showError('Failed to load achievements. Please try again.');
    }
}

/**
 * Load statistics data from backend
 */
async function loadStatsData() {
    try {
        const response = await api.getStats();
        statsData = response.stats;
        updateStatsCards();
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

/**
 * Render achievements grid
 */
function renderAchievements() {
    const grid = document.getElementById('badgesGrid');
    if (!achievementsData || !achievementsData.achievements) {
        grid.innerHTML = '<p class="no-data">No achievements data available.</p>';
        return;
    }

    const achievements = achievementsData.achievements;
    
    // Filter achievements based on current filter
    const filteredAchievements = achievements.filter(achievement => {
        if (currentFilter === 'all') return true;
        if (currentFilter === 'unlocked') return achievement.earned;
        if (currentFilter === 'locked') return !achievement.earned;
        return true;
    });

    if (filteredAchievements.length === 0) {
        grid.innerHTML = `<p class="no-data">No ${currentFilter} achievements.</p>`;
        return;
    }

    grid.innerHTML = filteredAchievements.map(achievement => {
        const isEarned = achievement.earned;
        const statusClass = isEarned ? 'unlocked' : 'locked';
        const iconClass = isEarned ? 'unlocked-icon' : 'locked-icon';
        
        // Map icon_url to Font Awesome icons
        const iconMap = {
            'first-steps': 'fa-graduation-cap',
            'hot-streak': 'fa-fire',
            'card-creator': 'fa-plus-circle',
            'dedicated-learner': 'fa-calendar-check',
            'speed-demon': 'fa-bolt',
            'perfect-score': 'fa-star',
            'week-warrior': 'fa-calendar-week',
            'deck-builder': 'fa-layer-group',
            'flash-master': 'fa-crown',
            'early-bird': 'fa-sun',
            'night-owl': 'fa-moon',
            'consistency-king': 'fa-chart-line',
            'hundred-club': 'fa-hundred-points',
            'thousand-cards': 'fa-infinity',
            'deck-master': 'fa-chess-king',
            'perfectionist': 'fa-gem',
            'marathon-runner': 'fa-running',
            'brain-power': 'fa-brain',
            'lightning-fast': 'fa-zap',
            'scholar': 'fa-user-graduate',
            'legend': 'fa-trophy',
            'ultimate': 'fa-medal',
            'master-of-all': 'fa-crown',
            'collector': 'fa-dice-d20'
        };
        
        // Get icon from icon_url or use default
        let iconClass2 = 'fa-trophy';
        if (achievement.icon_url) {
            const iconKey = achievement.icon_url.toLowerCase().replace(/[^a-z-]/g, '');
            iconClass2 = iconMap[iconKey] || 'fa-trophy';
        }

        if (isEarned) {
            const earnedDate = achievement.earned_at ? 
                new Date(achievement.earned_at).toLocaleDateString('en-US', { 
                    month: 'short', 
                    day: 'numeric', 
                    year: 'numeric' 
                }) : 
                'Recently';

            return `
                <div class="badge-card ${statusClass}" data-status="${statusClass}">
                    <div class="badge-icon ${iconClass}">
                        <i class="fas ${iconClass2}"></i>
                    </div>
                    <h3 class="badge-title">${achievement.name}</h3>
                    <p class="badge-description">${achievement.description}</p>
                    <div class="badge-footer">
                        <span class="badge-date">
                            <i class="fas fa-check-circle"></i>
                            ${earnedDate}
                        </span>
                    </div>
                </div>
            `;
        } else {
            return `
                <div class="badge-card ${statusClass}" data-status="${statusClass}">
                    <div class="badge-icon ${iconClass}">
                        <i class="fas ${iconClass2}"></i>
                    </div>
                    <h3 class="badge-title">${achievement.name}</h3>
                    <p class="badge-description">${achievement.description}</p>
                    <div class="badge-footer">
                        <span class="badge-status">
                            <i class="fas fa-lock"></i>
                            Locked
                        </span>
                    </div>
                </div>
            `;
        }
    }).join('');
}

/**
 * Update achievement statistics
 */
function updateAchievementStats() {
    if (!achievementsData) return;

    const unlockedBadges = achievementsData.earned || 0;
    const totalBadges = achievementsData.total || 0;
    
    document.getElementById('unlockedBadges').textContent = unlockedBadges;
    document.getElementById('totalBadges').textContent = totalBadges;
}

/**
 * Update stats cards with backend data
 */
function updateStatsCards() {
    if (!statsData) return;

    const user = api.getCurrentUser();
    
    // Update total points - statsData already has the stats object directly
    const totalPoints = statsData.total_points || (user && user.points) || 0;
    
    document.getElementById('totalPoints').textContent = totalPoints.toLocaleString();
    
    // Calculate progress to next level (every 1000 points)
    const currentLevel = Math.floor(totalPoints / 1000);
    const pointsInLevel = totalPoints % 1000;
    const pointsToNext = 1000 - pointsInLevel;
    const progressPercent = (pointsInLevel / 1000) * 100;
    
    const progressBar = document.querySelector('.points-card .progress-fill');
    const progressText = document.querySelector('.points-card .progress-text');
    
    if (progressBar) progressBar.style.width = `${progressPercent}%`;
    if (progressText) progressText.textContent = `${pointsToNext} to next level`;
    
    // Update streak
    const streakValue = statsData.current_streak || 0;
    document.getElementById('currentStreak').textContent = streakValue;
    
    // Update motivation message
    updateMotivationMessage();
}

/**
 * Update motivation message based on user progress
 */
function updateMotivationMessage() {
    const messages = [
        {
            title: "You're doing great! 🌟",
            text: "Keep up the excellent work! Every card you review brings you closer to mastery."
        },
        {
            title: "Fantastic progress! 🚀",
            text: "Your dedication is impressive! Continue building your knowledge one card at a time."
        },
        {
            title: "Keep pushing forward! 💪",
            text: "You're making amazing progress! Consistency is the key to long-term learning success."
        },
        {
            title: "You're unstoppable! ⭐",
            text: "Your commitment to learning is inspiring! Keep reviewing and unlocking new achievements."
        }
    ];
    
    const randomMessage = messages[Math.floor(Math.random() * messages.length)];
    
    document.getElementById('motivationTitle').textContent = randomMessage.title;
    document.getElementById('motivationText').textContent = randomMessage.text;
}

/**
 * Filter badges
 */
function filterBadges(filter) {
    currentFilter = filter;
    
    // Update active tab
    document.querySelectorAll('.filter-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Re-render achievements
    renderAchievements();
}

/**
 * Get new motivation message
 */
function getNewMotivation() {
    updateMotivationMessage();
}

/**
 * Check for new achievements
 */
async function checkForNewAchievements() {
    try {
        const response = await api.checkAchievements();
        if (response.new_achievements && response.new_achievements.length > 0) {
            // Show notification for new achievements
            showNewAchievementNotification(response.new_achievements);
            // Reload achievements
            await loadAchievementsData();
        }
    } catch (error) {
        console.error('Failed to check achievements:', error);
    }
}

/**
 * Show new achievement notification
 */
function showNewAchievementNotification(achievements) {
    achievements.forEach(achievement => {
        // You can implement a toast notification here
        console.log('New achievement unlocked:', achievement.name);
    });
}

/**
 * Show error message
 */
function showError(message) {
    // You can implement a toast notification here
    alert(message);
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Check for new achievements periodically
    // Uncomment if you want auto-checking
    // setInterval(checkForNewAchievements, 60000); // Check every minute
}

// Make functions globally available
window.filterBadges = filterBadges;
window.getNewMotivation = getNewMotivation;
