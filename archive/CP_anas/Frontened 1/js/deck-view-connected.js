// Deck View connected to Flask backend

// Get deck ID from URL
const urlParams = new URLSearchParams(window.location.search);
const deckId = urlParams.get('deck');

if (!deckId) {
    alert('No deck specified');
    window.location.href = 'dashboard-connected.html';
}

// State
let currentDeck = null;
let cards = [];
let currentEditingCardId = null;
let currentDeletingCardId = null;

// Initialize deck view
async function initDeckView() {
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
        await loadCards();
    } catch (error) {
        console.error('Error loading deck:', error);
        alert('Failed to load deck: ' + error.message);
        window.location.href = 'dashboard-connected.html';
    }
}

// Load cards
async function loadCards() {
    const loadingState = document.getElementById('loadingState');
    const cardsContainer = document.getElementById('cardsList');

    try {
        // Load deck info first
        const deckResponse = await api.getDeck(deckId);
        currentDeck = deckResponse.deck;
        
        if (currentDeck) {
            document.querySelector('.deck-title').textContent = currentDeck.deck_name;
        }
        
        // Load cards
        const response = await api.getCards(deckId);
        cards = response.cards || [];

        // Hide loading state
        if (loadingState) {
            loadingState.style.display = 'none';
        }

        // Update card count
        updateCardCount();

        // Render cards
        renderCards();

    } catch (error) {
        console.error('Error loading cards:', error);
        if (loadingState) {
            loadingState.innerHTML = `
                <i class="fas fa-exclamation-circle"></i>
                <p>Error loading cards. Please try again.</p>
            `;
        }
        throw error;
    }
}

// Render cards
function renderCards() {
    const cardsContainer = document.getElementById('cardsList');
    cardsContainer.innerHTML = '';

    if (cards.length === 0) {
        cardsContainer.innerHTML = `
            <div class="empty-cards-state">
                <i class="fas fa-clone"></i>
                <h3>No cards yet</h3>
                <p>Add your first card to start studying!</p>
            </div>
        `;
        return;
    }

    cards.forEach((card, index) => {
        const cardElement = createCardElement(card, index + 1);
        cardsContainer.appendChild(cardElement);
    });
}

// Create card element
function createCardElement(card, index) {
    const div = document.createElement('div');
    div.className = 'card-item';
    div.setAttribute('data-card-id', card.card_id);

    // Determine status based on next_review_date
    let status = 'new';
    if (card.next_review_date) {
        const nextReview = new Date(card.next_review_date);
        const today = new Date();
        if (nextReview > today) {
            status = 'learning';
        } else {
            status = 'mastered';
        }
    }

    div.innerHTML = `
        <div class="card-number">
            <span>#${index}</span>
        </div>
        <div class="card-content">
            <div class="card-front">
                <label class="content-label">Question</label>
                <p class="content-text">${escapeHtml(card.front_content)}</p>
            </div>
            <div class="card-divider"></div>
            <div class="card-back">
                <label class="content-label">Answer</label>
                <p class="content-text preview">${escapeHtml(card.back_content)}</p>
            </div>
        </div>
        <div class="card-status">
            <span class="status-badge ${status}">${capitalizeFirst(status)}</span>
        </div>
        <div class="card-actions">
            <button class="action-icon-btn edit-btn" onclick="editCard(${card.card_id}, '${escapeHtml(card.front_content)}', '${escapeHtml(card.back_content)}')" title="Edit Card">
                <i class="fas fa-edit"></i>
            </button>
            <button class="action-icon-btn delete-btn" onclick="deleteCard(${card.card_id})" title="Delete Card">
                <i class="fas fa-trash-alt"></i>
            </button>
        </div>
    `;

    return div;
}

// Escape HTML
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML.replace(/'/g, '&#39;');
}

// Capitalize first letter
function capitalizeFirst(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

// Update card count
function updateCardCount() {
    document.querySelector('.card-count').textContent = `${cards.length} card${cards.length !== 1 ? 's' : ''}`;
}

// Open add card modal
function openAddCardModal() {
    const modal = document.getElementById('cardModal');
    const modalTitle = document.getElementById('modalTitle');
    const form = document.getElementById('cardForm');

    // Reset form
    form.reset();
    currentEditingCardId = null;

    // Set title
    modalTitle.textContent = 'Add New Card';

    // Show modal
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

// Edit card
function editCard(cardId, frontContent, backContent) {
    const modal = document.getElementById('cardModal');
    const modalTitle = document.getElementById('modalTitle');
    const cardFront = document.getElementById('cardFront');
    const cardBack = document.getElementById('cardBack');

    // Set current editing card
    currentEditingCardId = cardId;

    // Set title
    modalTitle.textContent = 'Edit Card';

    // Set content (decode HTML entities)
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = frontContent;
    cardFront.value = tempDiv.textContent;
    tempDiv.innerHTML = backContent;
    cardBack.value = tempDiv.textContent;

    // Show modal
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

// Close card modal
function closeCardModal() {
    const modal = document.getElementById('cardModal');
    modal.classList.remove('active');
    document.body.style.overflow = 'auto';
    currentEditingCardId = null;
    document.getElementById('cardError').style.display = 'none';
}

// Delete card
function deleteCard(cardId) {
    const modal = document.getElementById('deleteModal');
    currentDeletingCardId = cardId;

    // Show modal
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

// Close delete modal
function closeDeleteModal() {
    const modal = document.getElementById('deleteModal');
    modal.classList.remove('active');
    document.body.style.overflow = 'auto';
    currentDeletingCardId = null;
}

// Confirm delete
async function confirmDelete() {
    const deleteBtn = document.getElementById('confirmDeleteBtn');
    
    // Disable button
    deleteBtn.disabled = true;
    deleteBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Deleting...';
    
    try {
        await api.deleteCard(currentDeletingCardId);
        
        // Close modal
        closeDeleteModal();
        
        // Reload cards
        await loadCards();
        
    } catch (error) {
        alert('Failed to delete card: ' + error.message);
    } finally {
        deleteBtn.disabled = false;
        deleteBtn.innerHTML = '<i class="fas fa-trash"></i> Delete Card';
    }
}

// Start study session
function startStudySession() {
    window.location.href = `study-session.html?deck=${deckId}`;
}

// Handle card form submission
document.getElementById('cardForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const frontContent = document.getElementById('cardFront').value;
    const backContent = document.getElementById('cardBack').value;
    const saveBtn = document.querySelector('#cardForm button[type="submit"]');
    const errorDiv = document.getElementById('cardError');

    // Disable button
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
    errorDiv.style.display = 'none';

    try {
        if (currentEditingCardId) {
            // Update existing card
            await api.updateCard(currentEditingCardId, frontContent, backContent);

            // Close modal
            closeCardModal();

            // Reload cards
            await loadCards();
        } else {
            // Create new card
            await api.createCard(deckId, frontContent, backContent);

            // Close modal
            closeCardModal();

            // Reload cards
            await loadCards();
        }

    } catch (error) {
        errorDiv.textContent = error.message || 'Failed to save card';
        errorDiv.style.display = 'block';
    } finally {
        saveBtn.disabled = false;
        saveBtn.innerHTML = '<i class="fas fa-save"></i> Save Card';
    }
});

// Close modal on escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeCardModal();
        closeDeleteModal();
        closeUploadModal();
    }
});

// ========================================
// CSV UPLOAD FUNCTIONALITY
// ========================================

let parsedCSVData = null;

/**
 * Open CSV upload modal
 */
function openUploadModal() {
    const modal = document.getElementById('uploadModal');
    const form = document.getElementById('uploadForm');
    
    // Reset form
    form.reset();
    parsedCSVData = null;
    document.getElementById('uploadPreview').style.display = 'none';
    document.getElementById('uploadError').style.display = 'none';
    
    // Show modal
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

/**
 * Close CSV upload modal
 */
function closeUploadModal() {
    const modal = document.getElementById('uploadModal');
    modal.classList.remove('active');
    document.body.style.overflow = 'auto';
    parsedCSVData = null;
}

/**
 * Parse CSV file
 */
function parseCSV(text) {
    const lines = text.split('\n').filter(line => line.trim());
    if (lines.length < 2) {
        throw new Error('CSV file must have at least a header row and one data row');
    }
    
    // Parse header
    const headers = lines[0].split(',').map(h => h.trim().replace(/['"]/g, ''));
    
    // Find question and answer column indices
    let questionIdx = headers.findIndex(h => 
        h.toLowerCase() === 'question' || 
        h.toLowerCase() === 'front' || 
        h.toLowerCase() === 'front_content'
    );
    let answerIdx = headers.findIndex(h => 
        h.toLowerCase() === 'answer' || 
        h.toLowerCase() === 'back' || 
        h.toLowerCase() === 'back_content'
    );
    
    // If not found, assume first two columns
    if (questionIdx === -1) questionIdx = 0;
    if (answerIdx === -1) answerIdx = 1;
    
    // Parse data rows
    const cards = [];
    for (let i = 1; i < lines.length; i++) {
        const line = lines[i].trim();
        if (!line) continue;
        
        // Simple CSV parser (handles basic cases)
        const values = parseCSVLine(line);
        
        if (values.length > Math.max(questionIdx, answerIdx)) {
            const question = values[questionIdx].trim();
            const answer = values[answerIdx].trim();
            
            if (question && answer) {
                cards.push({
                    Question: question,
                    Answer: answer
                });
            }
        }
    }
    
    return cards;
}

/**
 * Parse a single CSV line (handles quoted fields)
 */
function parseCSVLine(line) {
    const result = [];
    let current = '';
    let inQuotes = false;
    
    for (let i = 0; i < line.length; i++) {
        const char = line[i];
        
        if (char === '"') {
            inQuotes = !inQuotes;
        } else if (char === ',' && !inQuotes) {
            result.push(current.trim().replace(/^["']|["']$/g, ''));
            current = '';
        } else {
            current += char;
        }
    }
    
    // Add last field
    result.push(current.trim().replace(/^["']|["']$/g, ''));
    return result;
}

/**
 * Handle file selection and preview
 */
document.getElementById('csvFile').addEventListener('change', async (e) => {
    const file = e.target.files[0];
    const errorDiv = document.getElementById('uploadError');
    const previewDiv = document.getElementById('uploadPreview');
    const previewContent = document.getElementById('previewContent');
    
    errorDiv.style.display = 'none';
    previewDiv.style.display = 'none';
    parsedCSVData = null;
    
    if (!file) return;
    
    // Check file size (5MB max)
    if (file.size > 5 * 1024 * 1024) {
        errorDiv.textContent = 'File size exceeds 5MB limit';
        errorDiv.style.display = 'block';
        e.target.value = '';
        return;
    }
    
    // Check file type
    if (!file.name.endsWith('.csv')) {
        errorDiv.textContent = 'Please select a CSV file';
        errorDiv.style.display = 'block';
        e.target.value = '';
        return;
    }
    
    try {
        // Read file
        const text = await file.text();
        
        // Parse CSV
        parsedCSVData = parseCSV(text);
        
        if (parsedCSVData.length === 0) {
            errorDiv.textContent = 'No valid cards found in CSV file';
            errorDiv.style.display = 'block';
            return;
        }
        
        // Show preview
        const previewCards = parsedCSVData.slice(0, 5);
        previewContent.innerHTML = previewCards.map((card, idx) => `
            <div style="padding: 8px; border-bottom: 1px solid #e2e8f0;">
                <strong style="color: #1e40af;">Card ${idx + 1}:</strong><br>
                <span style="font-size: 13px; color: #475569;">
                    Q: ${escapeHtml(card.Question)}<br>
                    A: ${escapeHtml(card.Answer)}
                </span>
            </div>
        `).join('');
        
        previewDiv.style.display = 'block';
        
        // Show summary
        const summary = document.createElement('p');
        summary.style.marginTop = '10px';
        summary.style.fontSize = '13px';
        summary.style.color = '#059669';
        summary.style.fontWeight = 'bold';
        summary.innerHTML = `<i class="fas fa-check-circle"></i> Found ${parsedCSVData.length} card(s) ready to upload`;
        previewContent.appendChild(summary);
        
    } catch (error) {
        console.error('CSV parsing error:', error);
        errorDiv.textContent = 'Error parsing CSV: ' + error.message;
        errorDiv.style.display = 'block';
        parsedCSVData = null;
    }
});

/**
 * Handle CSV upload form submission
 */
document.getElementById('uploadForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const uploadBtn = document.getElementById('uploadBtn');
    const errorDiv = document.getElementById('uploadError');
    
    if (!parsedCSVData || parsedCSVData.length === 0) {
        errorDiv.textContent = 'Please select a valid CSV file';
        errorDiv.style.display = 'block';
        return;
    }
    
    // Disable button
    uploadBtn.disabled = true;
    uploadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Uploading...';
    errorDiv.style.display = 'none';
    
    try {
        // Upload cards
        const response = await api.uploadCardsBulk(deckId, parsedCSVData);
        
        // Show success message
        const successMsg = response.failed > 0
            ? `Successfully added ${response.inserted} card(s). ${response.failed} card(s) failed.`
            : `Successfully added ${response.inserted} card(s)!`;
        
        alert(successMsg);
        
        // Close modal
        closeUploadModal();
        
        // Reload cards
        await loadCards();
        
    } catch (error) {
        console.error('Upload error:', error);
        errorDiv.textContent = error.message || 'Failed to upload cards';
        errorDiv.style.display = 'block';
    } finally {
        uploadBtn.disabled = false;
        uploadBtn.innerHTML = '<i class="fas fa-upload"></i> Upload Cards';
    }
});

// Initialize on page load
document.addEventListener('DOMContentLoaded', initDeckView);
