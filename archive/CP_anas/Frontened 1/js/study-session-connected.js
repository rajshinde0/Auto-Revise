// Study Session connected to Flask backend

// Get deck ID from URL if studying specific deck
const urlParams = new URLSearchParams(window.location.search);
const deckId = urlParams.get('deck');

// State
let dueCards = [];
let currentCardIndex = 0;
let isFlipped = false;
let sessionStats = {
    completed: 0,
    forgot: 0,
    hard: 0,
    good: 0,
    easy: 0,
    points: 0
};
let startTime = Date.now();

// Initialize study session
async function initStudySession() {
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

    try {
        // Load due cards
        const response = deckId 
            ? await api.getDeckStudySession(deckId)
            : await api.getStudySession();

        // Backend returns { cards: [...], total: n }
        dueCards = response.cards || [];

        if (dueCards.length === 0) {
            showNoCardsMessage();
            return;
        }

        // Update UI
        updateProgress();
        loadCard(0);

    } catch (error) {
        console.error('Error loading study session:', error);
        alert('Failed to load study session: ' + error.message);
        window.location.href = 'dashboard-connected.html';
    }
}

// Show no cards message
function showNoCardsMessage() {
    document.querySelector('.flashcard-container').innerHTML = `
        <div class="no-cards-message">
            <i class="fas fa-check-circle"></i>
            <h2>All Done!</h2>
            <p>You have no cards due for review right now.</p>
            <button class="btn-primary" onclick="window.location.href='dashboard-connected.html'">
                Back to Dashboard
            </button>
        </div>
    `;
    document.getElementById('ratingButtons').style.display = 'none';
}

// Load card
function loadCard(index) {
    if (index >= dueCards.length) {
        showSessionComplete();
        return;
    }

    const card = dueCards[index];
    currentCardIndex = index;
    isFlipped = false;

    // Update card content
    document.getElementById('questionText').textContent = card.front_content;
    document.getElementById('answerText').textContent = card.back_content;

    // Update deck name if available
    if (card.deck_name) {
        document.querySelector('.deck-name').textContent = card.deck_name;
    }

    // Reset card state
    const flashcard = document.getElementById('flashcard');
    flashcard.classList.remove('flipped', 'slide-out', 'slide-in');
    
    // Disable rating buttons
    const ratingButtons = document.querySelectorAll('.rating-btn');
    ratingButtons.forEach(btn => btn.disabled = true);

    // Show flip instruction
    const flipInstruction = document.getElementById('flipInstruction');
    if (flipInstruction && index === 0) {
        flipInstruction.style.display = 'flex';
        flipInstruction.style.opacity = '1';
    }

    // Update progress
    updateProgress();

    // Add slide-in animation
    setTimeout(() => {
        flashcard.classList.add('slide-in');
        setTimeout(() => {
            flashcard.classList.remove('slide-in');
        }, 400);
    }, 50);
}

// Flip card
function flipCard() {
    if (isFlipped) return;

    isFlipped = true;
    const flashcard = document.getElementById('flashcard');
    flashcard.classList.add('flipped');

    // Enable rating buttons
    const ratingButtons = document.querySelectorAll('.rating-btn');
    ratingButtons.forEach(btn => btn.disabled = false);

    // Hide flip instruction
    const flipInstruction = document.getElementById('flipInstruction');
    if (flipInstruction) {
        flipInstruction.style.opacity = '0';
        setTimeout(() => {
            flipInstruction.style.display = 'none';
        }, 300);
    }
}

// Rate card
async function rateCard(rating) {
    if (!isFlipped) return;

    const card = dueCards[currentCardIndex];

    try {
        // Submit review to backend (pass card_id and rating as separate parameters)
        await api.submitReview(card.card_id, rating);

        // Update session stats
        sessionStats.completed++;
        sessionStats[rating]++;
        
        // Calculate points
        const points = { forgot: 5, hard: 10, good: 15, easy: 20 };
        sessionStats.points += points[rating];

        // Update stats display
        document.getElementById('cardsCompleted').textContent = sessionStats.completed;
        document.getElementById('pointsEarned').textContent = sessionStats.points;

        // Slide out animation
        const flashcard = document.getElementById('flashcard');
        flashcard.classList.add('slide-out');

        setTimeout(() => {
            // Load next card
            loadCard(currentCardIndex + 1);
        }, 400);

    } catch (error) {
        console.error('Error submitting review:', error);
        alert('Failed to submit review: ' + error.message);
    }
}

// Update progress
function updateProgress() {
    const current = currentCardIndex + 1;
    const total = dueCards.length;
    const percent = Math.round((currentCardIndex / total) * 100);

    document.getElementById('currentCard').textContent = current;
    document.getElementById('totalCards').textContent = total;
    document.getElementById('progressPercent').textContent = percent;
    document.getElementById('progressFill').style.width = percent + '%';
}

// Show session complete
function showSessionComplete() {
    const totalTime = Math.floor((Date.now() - startTime) / 1000);
    const minutes = Math.floor(totalTime / 60);
    const seconds = totalTime % 60;

    const message = `
        <div class="session-complete">
            <i class="fas fa-trophy"></i>
            <h2>Session Complete!</h2>
            <div class="complete-stats">
                <div class="complete-stat">
                    <span class="stat-value">${sessionStats.completed}</span>
                    <span class="stat-label">Cards Reviewed</span>
                </div>
                <div class="complete-stat">
                    <span class="stat-value">${sessionStats.points}</span>
                    <span class="stat-label">Points Earned</span>
                </div>
                <div class="complete-stat">
                    <span class="stat-value">${minutes}:${seconds.toString().padStart(2, '0')}</span>
                    <span class="stat-label">Time Spent</span>
                </div>
            </div>
            <div class="rating-breakdown">
                <h3>Ratings</h3>
                <div class="breakdown-items">
                    <div class="breakdown-item">
                        <span class="breakdown-label forgot">Forgot</span>
                        <span class="breakdown-value">${sessionStats.forgot}</span>
                    </div>
                    <div class="breakdown-item">
                        <span class="breakdown-label hard">Hard</span>
                        <span class="breakdown-value">${sessionStats.hard}</span>
                    </div>
                    <div class="breakdown-item">
                        <span class="breakdown-label good">Good</span>
                        <span class="breakdown-value">${sessionStats.good}</span>
                    </div>
                    <div class="breakdown-item">
                        <span class="breakdown-label easy">Easy</span>
                        <span class="breakdown-value">${sessionStats.easy}</span>
                    </div>
                </div>
            </div>
            <button class="btn-primary" onclick="window.location.href='dashboard-connected.html'">
                <i class="fas fa-home"></i>
                Back to Dashboard
            </button>
        </div>
    `;

    document.querySelector('.flashcard-container').innerHTML = message;
    document.getElementById('ratingButtons').style.display = 'none';
}

// Timer
setInterval(() => {
    const elapsed = Math.floor((Date.now() - startTime) / 1000);
    const minutes = Math.floor(elapsed / 60);
    const seconds = elapsed % 60;
    const timerElement = document.getElementById('timer');
    if (timerElement) {
        timerElement.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }
}, 1000);

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    if (!isFlipped && e.code === 'Space') {
        e.preventDefault();
        flipCard();
    } else if (isFlipped) {
        switch(e.key) {
            case '1':
                rateCard('forgot');
                break;
            case '2':
                rateCard('hard');
                break;
            case '3':
                rateCard('good');
                break;
            case '4':
                rateCard('easy');
                break;
        }
    }
});

// Card click to flip
document.addEventListener('DOMContentLoaded', () => {
    const flashcard = document.getElementById('flashcard');
    if (flashcard) {
        flashcard.addEventListener('click', flipCard);
    }
    initStudySession();
});

// Make rateCard globally available
window.rateCard = rateCard;
