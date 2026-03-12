// Dashboard functionality connected to Flask backend

// State
let decks = [];
let stats = {};

// Initialize dashboard
async function initDashboard() {
    try {
        // First, verify authentication with backend
        if (!api.isLoggedIn()) {
            console.log('No user in localStorage, redirecting to login');
            window.location.href = 'login-page.html';
            return;
        }

        console.log('User found in localStorage:', api.getCurrentUser());

        // Verify session is still valid
        try {
            console.log('Verifying session with backend...');
            const userData = await api.me();
            console.log('Session verified successfully:', userData);
            // Update user data in case it changed
            document.getElementById('username').textContent = userData.user.username;
            
            // Show admin link if user is admin
            if (userData.user.is_admin) {
                const adminLink = document.getElementById('adminLink');
                if (adminLink) {
                    adminLink.style.display = 'inline-block';
                }
            }
        } catch (error) {
            // Session expired or invalid
            console.error('Session validation failed:', error);
            
            // Check if it's a 401 error (authentication required)
            if (error.message.includes('Authentication required')) {
                console.log('Session expired, clearing localStorage and redirecting to login');
                localStorage.removeItem('autorevise_user');
                alert('Your session has expired. Please login again.');
                window.location.href = 'login-page.html';
                return;
            }
            
            // For other errors, try to continue anyway
            console.warn('Session validation had an error, but attempting to continue:', error);
            const user = api.getCurrentUser();
            if (user && user.username) {
                document.getElementById('username').textContent = user.username;
            }
        }

        // Load dashboard data
        console.log('Loading dashboard data...');
        await Promise.all([
            loadStats(),
            loadDecks()
        ]);
        console.log('Dashboard loaded successfully');
    } catch (error) {
        console.error('Error initializing dashboard:', error);
        if (error.message.includes('Authentication required')) {
            localStorage.removeItem('autorevise_user');
            alert('Authentication error. Please login again.');
            window.location.href = 'login-page.html';
        }
    }
}

// Load user statistics
async function loadStats() {
    try {
        const response = await api.getStats();
        stats = response.stats;

        // Update stat cards
        document.getElementById('totalDecks').textContent = stats.total_decks || 0;
        document.getElementById('totalCards').textContent = stats.total_cards || 0;
        document.getElementById('cardsDue').textContent = stats.cards_due || 0;
        document.getElementById('cardsUpcoming').textContent = stats.cards_upcoming || 0;

        // Show study now section if cards are due
        if (stats.cards_due > 0) {
            document.getElementById('studyNowSection').style.display = 'block';
            document.getElementById('dueCount').textContent = stats.cards_due;
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Load all decks
async function loadDecks() {
    const container = document.getElementById('decksContainer');
    const loadingState = document.getElementById('loadingState');
    const emptyState = document.getElementById('emptyState');

    try {
        const response = await api.getDecks();
        decks = response.decks;

        // Hide loading state
        if (loadingState) {
            loadingState.style.display = 'none';
        }

        if (!decks || decks.length === 0) {
            if (emptyState) {
                emptyState.style.display = 'flex';
            }
            return;
        }

        // Hide empty state
        if (emptyState) {
            emptyState.style.display = 'none';
        }

        // Clear container
        if (container) {
            container.innerHTML = '';

            // Render decks
            decks.forEach(deck => {
                const deckCard = createDeckCard(deck);
                container.appendChild(deckCard);
            });
        }

    } catch (error) {
        console.error('Error loading decks:', error);
        if (loadingState) {
            loadingState.innerHTML = `
                <i class="fas fa-exclamation-circle"></i>
                <p>Error loading decks. Please try again.</p>
            `;
        }
    }
}

// Create deck card element
function createDeckCard(deck) {
    const card = document.createElement('div');
    card.className = 'deck-card';
    card.innerHTML = `
        <div class="deck-header">
            <div class="deck-icon">
                <i class="fas fa-layer-group"></i>
            </div>
            <h3>${escapeHtml(deck.deck_name)}</h3>
        </div>
        <div class="deck-body">
            <p class="deck-description">${escapeHtml(deck.description) || 'No description'}</p>
            <div class="deck-stats">
                <span class="deck-stat">
                    <i class="fas fa-clone"></i>
                    ${deck.card_count || 0} cards
                </span>
            </div>
        </div>
        <div class="deck-actions">
            <button class="btn-secondary" onclick="viewDeck(${deck.deck_id})">
                <i class="fas fa-eye"></i>
                View Cards
            </button>
            <button class="btn-primary" onclick="studyDeck(${deck.deck_id})">
                <i class="fas fa-play"></i>
                Study
            </button>
        </div>
    `;
    return card;
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Start general study session
function startStudy() {
    window.location.href = 'study-session.html';
}

// Study specific deck
function studyDeck(deckId) {
    window.location.href = `study-session.html?deck=${deckId}`;
}

// View deck cards
function viewDeck(deckId) {
    window.location.href = `deck-view.html?deck=${deckId}`;
}

// Create Deck Modal Functions
function openCreateDeckModal() {
    document.getElementById('createDeckModal').classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeCreateDeckModal() {
    document.getElementById('createDeckModal').classList.remove('active');
    document.body.style.overflow = 'auto';
    document.getElementById('createDeckForm').reset();
    document.getElementById('createDeckError').style.display = 'none';
}

// Handle create deck form
document.getElementById('createDeckForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const deckName = document.getElementById('deckName').value;
    const description = document.getElementById('deckDescription').value;
    const createBtn = document.getElementById('createDeckBtn');
    const errorDiv = document.getElementById('createDeckError');

    // Disable button
    createBtn.disabled = true;
    createBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating...';

    try {
        const response = await api.createDeck(deckName, description);

        // Close modal
        closeCreateDeckModal();

        // Reload decks and stats
        await Promise.all([loadDecks(), loadStats()]);

    } catch (error) {
        errorDiv.textContent = error.message || 'Failed to create deck';
        errorDiv.style.display = 'block';
    } finally {
        createBtn.disabled = false;
        createBtn.innerHTML = '<i class="fas fa-plus"></i> Create Deck';
    }
});

// Handle logout
async function handleLogout() {
    if (confirm('Are you sure you want to logout?')) {
        try {
            await api.logout();
            window.location.href = 'login-page.html';
        } catch (error) {
            console.error('Logout error:', error);
            // Clear local data anyway
            localStorage.removeItem('autorevise_user');
            window.location.href = 'login-page.html';
        }
    }
}

// Close modal on escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeCreateDeckModal();
    }
});

// Initialize on page load
document.addEventListener('DOMContentLoaded', initDashboard);
