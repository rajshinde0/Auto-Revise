-- ==========================================================
-- MCQ Feature: Database Schema Updates
-- ==========================================================

USE autorevise_db;

-- 1. Add is_admin column to Users table (only if it doesn't exist)
-- Note: If column already exists, this will throw an error - safe to ignore
ALTER TABLE Users 
ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT FALSE;

-- 2. Create MCQ_Questions table
CREATE TABLE IF NOT EXISTS MCQ_Questions (
    mcq_id INT PRIMARY KEY AUTO_INCREMENT,
    deck_id INT NOT NULL,
    question_text TEXT NOT NULL,
    option_a VARCHAR(500) NOT NULL,
    option_b VARCHAR(500) NOT NULL,
    option_c VARCHAR(500) NOT NULL,
    option_d VARCHAR(500) NOT NULL,
    correct_option ENUM('A', 'B', 'C', 'D') NOT NULL,
    explanation TEXT NULL,
    difficulty ENUM('easy', 'medium', 'hard') DEFAULT 'medium',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INT NOT NULL,
    FOREIGN KEY (deck_id) REFERENCES Decks(deck_id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES Users(user_id) ON DELETE CASCADE,
    INDEX idx_deck_mcq (deck_id),
    INDEX idx_difficulty (difficulty)
) ENGINE=InnoDB;

-- 3. Create MCQ_Performance table (tracks user's MCQ attempts)
CREATE TABLE IF NOT EXISTS MCQ_Performance (
    mcq_performance_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    mcq_id INT NOT NULL,
    last_attempt_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    times_attempted INT NOT NULL DEFAULT 0,
    times_correct INT NOT NULL DEFAULT 0,
    next_review_date DATE NULL,
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (mcq_id) REFERENCES MCQ_Questions(mcq_id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_mcq (user_id, mcq_id),
    INDEX idx_next_review (next_review_date)
) ENGINE=InnoDB;

-- 4. Create MCQ_Upload_Log table (tracks admin uploads)
CREATE TABLE IF NOT EXISTS MCQ_Upload_Log (
    upload_id INT PRIMARY KEY AUTO_INCREMENT,
    admin_id INT NOT NULL,
    filename VARCHAR(255) NOT NULL,
    total_questions INT NOT NULL,
    successful_imports INT NOT NULL,
    failed_imports INT NOT NULL,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_id) REFERENCES Users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 5. Make the first user an admin (for testing)
-- UPDATE Users SET is_admin = TRUE WHERE user_id = 1;

-- ==========================================================
-- Sample MCQ Data (optional, for testing)
-- ==========================================================

-- First, create a sample deck if needed
-- INSERT INTO Decks (user_id, deck_name, description) 
-- VALUES (1, 'Sample MCQ Deck', 'Test deck for MCQ questions');

-- Insert sample MCQs (adjust deck_id and created_by as needed)
-- INSERT INTO MCQ_Questions (deck_id, question_text, option_a, option_b, option_c, option_d, correct_option, explanation, difficulty, created_by) VALUES
-- (1, 'What is the capital of France?', 'London', 'Berlin', 'Paris', 'Madrid', 'C', 'Paris is the capital and largest city of France.', 'easy', 1),
-- (1, 'Which programming language is known for its use in data science?', 'Java', 'Python', 'C++', 'Ruby', 'B', 'Python has extensive libraries for data science like NumPy, Pandas, and scikit-learn.', 'medium', 1);

SELECT 'MCQ tables created successfully!' AS Status;

SHOW TABLES;
