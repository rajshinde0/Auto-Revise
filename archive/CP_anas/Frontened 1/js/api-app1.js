/**
 * AutoRevise API Service for App1.py Backend
 * Complete API integration for all frontend pages
 */

class AutoReviseAPI {
    constructor() {
        this.baseURL = 'http://127.0.0.1:5000';
        this.user = this.loadUserFromStorage();
    }

    /**
     * Load user data from localStorage
     */
    loadUserFromStorage() {
        const userData = localStorage.getItem('autorevise_user');
        return userData ? JSON.parse(userData) : null;
    }

    /**
     * Save user data to localStorage
     */
    saveUserToStorage(user) {
        if (user) {
            localStorage.setItem('autorevise_user', JSON.stringify(user));
            this.user = user;
        } else {
            localStorage.removeItem('autorevise_user');
            this.user = null;
        }
    }

    /**
     * Check if user is logged in
     */
    isLoggedIn() {
        return this.user !== null && this.user.user_id;
    }

    /**
     * Get current user
     */
    getCurrentUser() {
        return this.user;
    }

    /**
     * Make API request with error handling
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            credentials: 'include', // Important for session cookies
            ...options
        };

        try {
            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || `HTTP error! status: ${response.status}`);
            }

            return data;
        } catch (error) {
            console.error('API Request Error:', error);
            throw error;
        }
    }

    // ========================================
    // AUTHENTICATION ENDPOINTS
    // ========================================

    /**
     * Register a new user
     */
    async register(username, email, password) {
        const data = await this.request('/register', {
            method: 'POST',
            body: JSON.stringify({ username, email, password })
        });

        if (data.user) {
            this.saveUserToStorage(data.user);
        }
        
        return data;
    }

    /**
     * Login user
     */
    async login(email, password) {
        const data = await this.request('/login', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });
        
        if (data.user) {
            this.saveUserToStorage(data.user);
        }
        
        return data;
    }

    /**
     * Logout user
     */
    async logout() {
        try {
            await this.request('/logout', { method: 'POST' });
        } finally {
            this.saveUserToStorage(null);
        }
    }

    /**
     * Get current logged-in user info
     */
    async me() {
        const data = await this.request('/me');
        if (data.user) {
            this.saveUserToStorage(data.user);
        }
        return data;
    }

    // ========================================
    // DECK ENDPOINTS
    // ========================================

    /**
     * Get all decks
     */
    async getDecks() {
        return await this.request('/decks');
    }

    /**
     * Get a specific deck
     */
    async getDeck(deckId) {
        return await this.request(`/decks/${deckId}`);
    }

    /**
     * Create a new deck
     */
    async createDeck(deckName, description = '') {
        return await this.request('/decks', {
            method: 'POST',
            body: JSON.stringify({ deck_name: deckName, description })
        });
    }

    /**
     * Delete a deck
     */
    async deleteDeck(deckId) {
        return await this.request(`/decks/${deckId}`, {
            method: 'DELETE'
        });
    }

    // ========================================
    // CARD ENDPOINTS
    // ========================================

    /**
     * Get all cards in a deck
     */
    async getCards(deckId) {
        return await this.request(`/decks/${deckId}/cards`);
    }

    /**
     * Create a new card
     */
    async createCard(deckId, frontContent, backContent) {
        return await this.request(`/decks/${deckId}/cards`, {
            method: 'POST',
            body: JSON.stringify({ 
                front_content: frontContent, 
                back_content: backContent 
            })
        });
    }

    /**
     * Update a card
     */
    async updateCard(cardId, frontContent, backContent) {
        return await this.request(`/cards/${cardId}`, {
            method: 'PUT',
            body: JSON.stringify({ 
                front_content: frontContent, 
                back_content: backContent 
            })
        });
    }

    /**
     * Delete a card
     */
    async deleteCard(cardId) {
        return await this.request(`/cards/${cardId}`, {
            method: 'DELETE'
        });
    }

    /**
     * Bulk upload cards from CSV data
     */
    async uploadCardsBulk(deckId, cardsData) {
        return await this.request(`/decks/${deckId}/upload-cards`, {
            method: 'POST',
            body: JSON.stringify({ cards: cardsData })
        });
    }

    // ========================================
    // STUDY SESSION ENDPOINTS
    // ========================================

    /**
     * Get cards due for review (all decks)
     */
    async getStudySession() {
        return await this.request('/study-session');
    }

    /**
     * Get cards due for review (specific deck)
     */
    async getDeckStudySession(deckId) {
        return await this.request(`/study-session?deck_id=${deckId}`);
    }

    /**
     * Submit a card review
     */
    async submitReview(cardId, rating) {
        return await this.request('/submit-review', {
            method: 'POST',
            body: JSON.stringify({ card_id: cardId, rating })
        });
    }

    // ========================================
    // STATISTICS ENDPOINTS
    // ========================================

    /**
     * Get user statistics
     */
    async getStats() {
        return await this.request('/stats');
    }

    // ========================================
    // ACHIEVEMENTS ENDPOINTS
    // ========================================

    /**
     * Get all achievements and user's progress
     */
    async getAchievements() {
        return await this.request('/achievements');
    }

    /**
     * Check for new achievements
     */
    async checkAchievements() {
        return await this.request('/check-achievements', {
            method: 'POST'
        });
    }
}

// Create global API instance
const api = new AutoReviseAPI();
