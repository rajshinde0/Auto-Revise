/**
 * Escape text before it goes into innerHTML.
 *
 * Question text and options are admin-authored free text. Interpolating them
 * into a template literal unescaped makes any saved markup execute when
 * another admin views the list - a stored XSS.
 */
function escapeHtml(value) {
    if (value === null || value === undefined) return '';
    return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

/**
 * Read an error message out of a JSON error body, whatever shape it uses.
 */
function errorMessage(result, fallback) {
    return (result && (result.error || result.message)) || fallback;
}

// Tab switching
// `evt` is passed in from the onclick handler; this used to rely on the
// non-standard implicit `window.event` global, which breaks if the function
// is ever called any other way.
function showTab(tabName, evt) {
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    document.getElementById(`${tabName}-tab`).classList.add('active');

    const trigger = (evt && evt.currentTarget) ||
                    document.querySelector(`.tab-btn[data-tab="${tabName}"]`);
    if (trigger) {
        trigger.classList.add('active');
    }
}

// Add Question
document.getElementById('add-form')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    const formData = new FormData(this);
    const data = Object.fromEntries(formData);
    
    try {
        const response = await fetch('/api/questions', {
            method: 'POST',
            headers: {'Content-Type': 'application/json', 'X-CSRFToken': window.CSRF_TOKEN},
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        if (response.ok) {
            alert('Question added successfully!');
            this.reset();
        } else {
            alert('Error: ' + errorMessage(result, 'Could not add the question.'));
        }
    } catch (error) {
        alert('Failed to add question: ' + error.message);
    }
});

// Load all questions
async function loadQuestions() {
    const subject = document.getElementById('subject-filter').value;
    const url = subject
        ? `/api/questions?subject=${encodeURIComponent(subject)}`
        : '/api/questions';

    const listDiv = document.getElementById('questions-list');

    try {
        const response = await fetch(url);

        // Check the status before assuming an array came back: an error body
        // is an object, and questions.map would then throw a TypeError that
        // the catch below would report as a misleading generic failure.
        if (!response.ok) {
            const result = await response.json().catch(() => null);
            listDiv.innerHTML = '<p class="empty-state"></p>';
            listDiv.firstChild.textContent =
                errorMessage(result, `Could not load questions (${response.status}).`);
            return;
        }

        const questions = await response.json();

        if (!Array.isArray(questions) || questions.length === 0) {
            listDiv.innerHTML = '<p class="empty-state">No questions found</p>';
            return;
        }

        listDiv.innerHTML = questions.map(q => `
            <div class="question-item">
                <strong>ID: ${escapeHtml(q.q_id)}</strong> |
                <span class="subject-badge">${escapeHtml(q.subject)}</span>
                <p><strong>Q:</strong> ${escapeHtml(q.question_text)}</p>
                <p><strong>A:</strong> ${escapeHtml(q.option_a)} | <strong>B:</strong> ${escapeHtml(q.option_b)}</p>
                <p><strong>C:</strong> ${escapeHtml(q.option_c)} | <strong>D:</strong> ${escapeHtml(q.option_d)}</p>
                <p><strong>Correct:</strong> ${escapeHtml(q.correct_option)}</p>
            </div>
        `).join('');
    } catch (error) {
        alert('Failed to load questions: ' + error.message);
    }
}

// Search questions
function searchQuestions() {
    const searchTerm = document.getElementById('search-box').value.toLowerCase();
    const items = document.querySelectorAll('.question-item');
    
    items.forEach(item => {
        const text = item.textContent.toLowerCase();
        item.style.display = text.includes(searchTerm) ? 'block' : 'none';
    });
}

// Load question data for update
async function loadQuestionData(qid) {
    if (!qid) return;
    
    try {
        const response = await fetch(`/api/questions/${qid}`);
        const question = await response.json();
        
        if (response.ok) {
            document.getElementById('update-q-id').value = question.q_id;
            document.getElementById('update-question').value = question.question_text;
            document.getElementById('update-option-a').value = question.option_a;
            document.getElementById('update-option-b').value = question.option_b;
            document.getElementById('update-option-c').value = question.option_c;
            document.getElementById('update-option-d').value = question.option_d;
            document.getElementById('update-correct').value = question.correct_option;
            document.getElementById('update-subject').value = question.subject;
        } else {
            alert('Question not found');
        }
    } catch (error) {
        alert('Failed to load question: ' + error.message);
    }
}

// Update question
document.getElementById('update-form')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    const formData = new FormData(this);
    const data = Object.fromEntries(formData);
    const qid = data.q_id;
    
    try {
        const response = await fetch(`/api/questions/${qid}`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json', 'X-CSRFToken': window.CSRF_TOKEN},
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        if (response.ok) {
            alert('Question updated successfully!');
        } else {
            alert('Error: ' + errorMessage(result, 'Could not update the question.'));
        }
    } catch (error) {
        alert('Failed to update question: ' + error.message);
    }
});

// Preview question for deletion
document.getElementById('delete-qid')?.addEventListener('change', async function() {
    const qid = this.value;
    if (!qid) {
        document.getElementById('delete-preview').innerHTML = '';
        return;
    }
    
    try {
        const response = await fetch(`/api/questions/${qid}`);
        const question = await response.json();
        
        if (response.ok) {
            document.getElementById('delete-preview').innerHTML = `
                <div class="question-item">
                    <strong>ID: ${escapeHtml(question.q_id)}</strong> |
                    <span class="subject-badge">${escapeHtml(question.subject)}</span>
                    <p><strong>Q:</strong> ${escapeHtml(question.question_text)}</p>
                    <p><strong>Correct Answer:</strong> ${escapeHtml(question.correct_option)}</p>
                </div>
            `;
        } else {
            document.getElementById('delete-preview').innerHTML = '<p>Question not found</p>';
        }
    } catch (error) {
        alert('Failed to load question: ' + error.message);
    }
});

// Delete question
async function deleteQuestion() {
    const qid = document.getElementById('delete-qid').value;
    if (!qid) {
        alert('Please enter a question ID');
        return;
    }
    
    if (!confirm('Are you sure you want to delete this question?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/questions/${qid}`, {
            method: 'DELETE',
            headers: {'X-CSRFToken': window.CSRF_TOKEN}
        });
        
        const result = await response.json();
        if (response.ok) {
            alert('Question deleted successfully!');
            document.getElementById('delete-qid').value = '';
            document.getElementById('delete-preview').innerHTML = '';
        } else {
            alert('Error: ' + errorMessage(result, 'Could not delete the question.'));
        }
    } catch (error) {
        alert('Failed to delete question: ' + error.message);
    }
}

// Load questions on page load
if (document.getElementById('questions-list')) {
    loadQuestions();
}
