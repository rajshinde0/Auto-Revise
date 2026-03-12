/**
 * Integration Example: Add MCQs to Existing Study Session
 * 
 * This file shows how to integrate MCQs into your existing study-session-connected.js
 * 
 * Key Changes:
 * 1. Fetch both flashcards AND MCQs
 * 2. Mix and shuffle them together
 * 3. Render based on item type
 * 4. Handle MCQ answers
 */

// ========================================
// STEP 1: Fetch Mixed Study Items
// ========================================

async function loadMixedStudySession(deckId, flashcardLimit = 20, mcqLimit = 10) {
    try {
        // Fetch flashcards (existing functionality)
        const flashcardsResponse = await api.getStudySession(deckId, flashcardLimit);
        const flashcards = flashcardsResponse.cards || [];
        
        // Fetch MCQs (new functionality)
        const mcqResponse = await fetch(
            `http://127.0.0.1:5000/mcq/study-session?deck_id=${deckId}&limit=${mcqLimit}`,
            { credentials: 'include' }
        );
        
        if (!mcqResponse.ok) {
            throw new Error('Failed to fetch MCQs');
        }
        
        const mcqData = await mcqResponse.json();
        const mcqs = mcqData.mcqs || [];
        
        // Combine both types
        const allItems = [
            ...flashcards.map(card => ({
                type: 'flashcard',
                id: card.card_id,
                ...card
            })),
            ...mcqs.map(mcq => ({
                type: 'mcq',
                id: mcq.mcq_id,
                ...mcq
            }))
        ];
        
        // Shuffle for variety
        return shuffleArray(allItems);
        
    } catch (error) {
        console.error('Error loading study session:', error);
        return [];
    }
}

// ========================================
// STEP 2: Shuffle Utility
// ========================================

function shuffleArray(array) {
    const shuffled = [...array];
    for (let i = shuffled.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled;
}

// ========================================
// STEP 3: Render Current Item
// ========================================

function renderStudyItem(item, container) {
    if (item.type === 'flashcard') {
        renderFlashcard(item, container);
    } else if (item.type === 'mcq') {
        renderMCQ(item, container);
    }
}

// ========================================
// STEP 4: Render Flashcard (Existing)
// ========================================

function renderFlashcard(card, container) {
    container.innerHTML = `
        <div class="flashcard ${card.isFlipped ? 'flipped' : ''}" onclick="flipCard()">
            <div class="card-front">
                <h3>Question</h3>
                <p>${card.front_content}</p>
                <small>Click to reveal answer</small>
            </div>
            <div class="card-back">
                <h3>Answer</h3>
                <p>${card.back_content}</p>
                <div class="rating-buttons">
                    <button onclick="rateCard(${card.card_id}, 'again')" class="btn-again">Again</button>
                    <button onclick="rateCard(${card.card_id}, 'hard')" class="btn-hard">Hard</button>
                    <button onclick="rateCard(${card.card_id}, 'good')" class="btn-good">Good</button>
                    <button onclick="rateCard(${card.card_id}, 'easy')" class="btn-easy">Easy</button>
                </div>
            </div>
        </div>
    `;
}

// ========================================
// STEP 5: Render MCQ (New)
// ========================================

function renderMCQ(mcq, container) {
    container.innerHTML = `
        <div class="mcq-container">
            <div class="mcq-header">
                <span class="mcq-badge">MCQ</span>
                <span class="difficulty-badge difficulty-${mcq.difficulty}">${mcq.difficulty}</span>
            </div>
            
            <div class="mcq-question">
                <h3>${mcq.question_text}</h3>
            </div>
            
            <div class="mcq-options" id="mcqOptions">
                <button class="mcq-option" onclick="selectMCQOption('${mcq.mcq_id}', 'A', this)">
                    <span class="option-letter">A</span>
                    <span class="option-text">${mcq.option_a}</span>
                </button>
                <button class="mcq-option" onclick="selectMCQOption('${mcq.mcq_id}', 'B', this)">
                    <span class="option-letter">B</span>
                    <span class="option-text">${mcq.option_b}</span>
                </button>
                <button class="mcq-option" onclick="selectMCQOption('${mcq.mcq_id}', 'C', this)">
                    <span class="option-letter">C</span>
                    <span class="option-text">${mcq.option_c}</span>
                </button>
                <button class="mcq-option" onclick="selectMCQOption('${mcq.mcq_id}', 'D', this)">
                    <span class="option-letter">D</span>
                    <span class="option-text">${mcq.option_d}</span>
                </button>
            </div>
            
            <div class="mcq-feedback" id="mcqFeedback" style="display: none;"></div>
            
            <button class="mcq-submit" id="submitMCQ" onclick="submitMCQAnswer('${mcq.mcq_id}')" disabled>
                Submit Answer
            </button>
        </div>
    `;
}

// ========================================
// STEP 6: Handle MCQ Selection
// ========================================

let selectedMCQAnswer = null;

function selectMCQOption(mcqId, option, button) {
    // Remove previous selection
    document.querySelectorAll('.mcq-option').forEach(btn => {
        btn.classList.remove('selected');
    });
    
    // Mark current selection
    button.classList.add('selected');
    selectedMCQAnswer = option;
    
    // Enable submit button
    document.getElementById('submitMCQ').disabled = false;
}

// ========================================
// STEP 7: Submit MCQ Answer
// ========================================

async function submitMCQAnswer(mcqId) {
    if (!selectedMCQAnswer) return;
    
    const submitBtn = document.getElementById('submitMCQ');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Checking...';
    
    try {
        const response = await fetch(`http://127.0.0.1:5000/mcq/${mcqId}/check`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ answer: selectedMCQAnswer })
        });
        
        if (!response.ok) {
            throw new Error('Failed to check answer');
        }
        
        const result = await response.json();
        
        // Show feedback
        showMCQFeedback(result);
        
        // Disable all option buttons
        document.querySelectorAll('.mcq-option').forEach(btn => {
            btn.disabled = true;
        });
        
        // Highlight correct answer
        highlightCorrectAnswer(result.correct_answer);
        
        // Update points display if exists
        if (result.points_earned > 0) {
            updatePointsDisplay(result.points_earned);
        }
        
        // Auto-advance after 3 seconds
        setTimeout(() => {
            nextStudyItem();
        }, 3000);
        
    } catch (error) {
        console.error('Error checking MCQ answer:', error);
        alert('Failed to check answer. Please try again.');
        submitBtn.disabled = false;
        submitBtn.textContent = 'Submit Answer';
    }
}

// ========================================
// STEP 8: Show MCQ Feedback
// ========================================

function showMCQFeedback(result) {
    const feedbackDiv = document.getElementById('mcqFeedback');
    feedbackDiv.style.display = 'block';
    
    if (result.correct) {
        feedbackDiv.className = 'mcq-feedback correct';
        feedbackDiv.innerHTML = `
            <div class="feedback-icon">✅</div>
            <h4>Correct!</h4>
            <p>You earned ${result.points_earned} points</p>
            ${result.explanation ? `<p class="explanation">${result.explanation}</p>` : ''}
        `;
    } else {
        feedbackDiv.className = 'mcq-feedback incorrect';
        feedbackDiv.innerHTML = `
            <div class="feedback-icon">❌</div>
            <h4>Incorrect</h4>
            <p>The correct answer was: <strong>${result.correct_answer}</strong></p>
            ${result.explanation ? `<p class="explanation">${result.explanation}</p>` : ''}
        `;
    }
}

// ========================================
// STEP 9: Highlight Correct Answer
// ========================================

function highlightCorrectAnswer(correctOption) {
    const options = document.querySelectorAll('.mcq-option');
    const letters = ['A', 'B', 'C', 'D'];
    
    options.forEach((btn, index) => {
        if (letters[index] === correctOption) {
            btn.classList.add('correct-answer');
        } else if (btn.classList.contains('selected')) {
            btn.classList.add('wrong-answer');
        }
    });
}

// ========================================
// STEP 10: CSS Styles for MCQs
// ========================================

const mcqStyles = `
    .mcq-container {
        background: white;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        max-width: 700px;
        margin: 0 auto;
    }
    
    .mcq-header {
        display: flex;
        justify-content: space-between;
        margin-bottom: 1.5rem;
    }
    
    .mcq-badge {
        background: #2196F3;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 4px;
        font-size: 0.9rem;
        font-weight: bold;
    }
    
    .difficulty-badge {
        padding: 0.3rem 0.8rem;
        border-radius: 4px;
        font-size: 0.9rem;
        font-weight: bold;
        text-transform: capitalize;
    }
    
    .difficulty-easy { background: #4CAF50; color: white; }
    .difficulty-medium { background: #FF9800; color: white; }
    .difficulty-hard { background: #F44336; color: white; }
    
    .mcq-question h3 {
        font-size: 1.3rem;
        margin-bottom: 1.5rem;
        color: #333;
        line-height: 1.6;
    }
    
    .mcq-options {
        display: flex;
        flex-direction: column;
        gap: 1rem;
        margin-bottom: 1.5rem;
    }
    
    .mcq-option {
        display: flex;
        align-items: center;
        padding: 1rem;
        border: 2px solid #e0e0e0;
        border-radius: 8px;
        background: white;
        cursor: pointer;
        transition: all 0.3s;
        text-align: left;
    }
    
    .mcq-option:hover:not(:disabled) {
        border-color: #2196F3;
        background: #f5f9ff;
        transform: translateY(-2px);
    }
    
    .mcq-option.selected {
        border-color: #2196F3;
        background: #e3f2fd;
    }
    
    .mcq-option.correct-answer {
        border-color: #4CAF50;
        background: #e8f5e9;
    }
    
    .mcq-option.wrong-answer {
        border-color: #F44336;
        background: #ffebee;
    }
    
    .mcq-option:disabled {
        cursor: not-allowed;
        opacity: 0.7;
    }
    
    .option-letter {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 35px;
        height: 35px;
        background: #2196F3;
        color: white;
        border-radius: 50%;
        font-weight: bold;
        margin-right: 1rem;
        flex-shrink: 0;
    }
    
    .mcq-option.selected .option-letter {
        background: #1976D2;
    }
    
    .mcq-option.correct-answer .option-letter {
        background: #4CAF50;
    }
    
    .mcq-option.wrong-answer .option-letter {
        background: #F44336;
    }
    
    .option-text {
        flex: 1;
        font-size: 1rem;
    }
    
    .mcq-submit {
        width: 100%;
        padding: 1rem;
        background: #4CAF50;
        color: white;
        border: none;
        border-radius: 8px;
        font-size: 1.1rem;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.3s;
    }
    
    .mcq-submit:hover:not(:disabled) {
        background: #45a049;
    }
    
    .mcq-submit:disabled {
        background: #ccc;
        cursor: not-allowed;
    }
    
    .mcq-feedback {
        margin-top: 1.5rem;
        padding: 1.5rem;
        border-radius: 8px;
        text-align: center;
    }
    
    .mcq-feedback.correct {
        background: #e8f5e9;
        border: 2px solid #4CAF50;
    }
    
    .mcq-feedback.incorrect {
        background: #ffebee;
        border: 2px solid #F44336;
    }
    
    .feedback-icon {
        font-size: 3rem;
        margin-bottom: 0.5rem;
    }
    
    .mcq-feedback h4 {
        margin: 0.5rem 0;
        font-size: 1.5rem;
    }
    
    .explanation {
        margin-top: 1rem;
        padding: 1rem;
        background: white;
        border-radius: 4px;
        font-style: italic;
        color: #555;
    }
`;

// Inject styles
const styleSheet = document.createElement("style");
styleSheet.textContent = mcqStyles;
document.head.appendChild(styleSheet);

// ========================================
// STEP 11: Example Usage
// ========================================

/*
// In your study-session-connected.js:

let studyItems = [];
let currentIndex = 0;

async function initStudySession() {
    const deckId = getDeckIdFromURL();
    studyItems = await loadMixedStudySession(deckId, 20, 10);
    
    if (studyItems.length === 0) {
        showEmptyMessage();
        return;
    }
    
    renderCurrentStudyItem();
}

function renderCurrentStudyItem() {
    if (currentIndex >= studyItems.length) {
        showCompletionMessage();
        return;
    }
    
    const item = studyItems[currentIndex];
    const container = document.getElementById('study-container');
    
    renderStudyItem(item, container);
}

function nextStudyItem() {
    currentIndex++;
    renderCurrentStudyItem();
}

// Initialize on page load
initStudySession();
*/
