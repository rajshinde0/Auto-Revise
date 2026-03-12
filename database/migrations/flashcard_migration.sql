-- ============================================================
-- FLASHCARD SYSTEM MIGRATION
-- Adds flashcard, deck, spaced repetition, and MCQ category features
-- Run this after the main database is set up
-- ============================================================

USE mcq_flashcards;

-- ============================================================
-- TABLE: decks - User flashcard decks
-- ============================================================
CREATE TABLE IF NOT EXISTS `decks` (
    `deck_id` INT PRIMARY KEY AUTO_INCREMENT,
    `user_id` INT NOT NULL,
    `deck_name` VARCHAR(100) NOT NULL,
    `description` TEXT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`user_id`) ON DELETE CASCADE,
    INDEX `idx_user_id` (`user_id`),
    INDEX `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- TABLE: cards - Flashcards within decks
-- ============================================================
CREATE TABLE IF NOT EXISTS `cards` (
    `card_id` INT PRIMARY KEY AUTO_INCREMENT,
    `deck_id` INT NOT NULL,
    `front_content` TEXT NOT NULL,
    `back_content` TEXT NOT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (`deck_id`) REFERENCES `decks`(`deck_id`) ON DELETE CASCADE,
    INDEX `idx_deck_id` (`deck_id`),
    FULLTEXT KEY `idx_card_content` (`front_content`, `back_content`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- TABLE: card_performance - SM-2 Spaced Repetition tracking
-- ============================================================
CREATE TABLE IF NOT EXISTS `card_performance` (
    `performance_id` INT PRIMARY KEY AUTO_INCREMENT,
    `user_id` INT NOT NULL,
    `card_id` INT NOT NULL,
    `next_review_date` DATE NOT NULL,
    `interval_days` INT NOT NULL DEFAULT 1,
    `ease_factor` DECIMAL(4,2) NOT NULL DEFAULT 2.50,
    `repetitions` INT NOT NULL DEFAULT 0,
    `last_reviewed` TIMESTAMP NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`user_id`) ON DELETE CASCADE,
    FOREIGN KEY (`card_id`) REFERENCES `cards`(`card_id`) ON DELETE CASCADE,
    UNIQUE KEY `unique_user_card` (`user_id`, `card_id`),
    INDEX `idx_user_review` (`user_id`, `next_review_date`),
    INDEX `idx_next_review` (`next_review_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- TABLE: study_log - Daily study session tracking
-- ============================================================
CREATE TABLE IF NOT EXISTS `study_log` (
    `log_id` INT PRIMARY KEY AUTO_INCREMENT,
    `user_id` INT NOT NULL,
    `study_date` DATE NOT NULL,
    `cards_reviewed` INT NOT NULL DEFAULT 0,
    `flashcards_reviewed` INT NOT NULL DEFAULT 0,
    `mcqs_reviewed` INT NOT NULL DEFAULT 0,
    `points_earned` INT NOT NULL DEFAULT 0,
    `study_duration_seconds` INT DEFAULT 0,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY `unique_user_day` (`user_id`, `study_date`),
    FOREIGN KEY (`user_id`) REFERENCES `users`(`user_id`) ON DELETE CASCADE,
    INDEX `idx_study_date` (`study_date`),
    INDEX `idx_user_date` (`user_id`, `study_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- TABLE: mcq_categories - MCQ Subject Categories
-- ============================================================
CREATE TABLE IF NOT EXISTS `mcq_categories` (
    `category_id` INT PRIMARY KEY AUTO_INCREMENT,
    `category_name` VARCHAR(100) NOT NULL UNIQUE,
    `description` TEXT NULL,
    `icon` VARCHAR(50) NULL,
    `color` VARCHAR(20) DEFAULT '#667eea',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_category_name` (`category_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- Insert default MCQ categories
-- ============================================================
INSERT INTO `mcq_categories` (`category_name`, `description`, `icon`, `color`) VALUES
('Physics', 'Mechanics, thermodynamics, electromagnetism, optics', '⚡', '#FF6B6B'),
('Chemistry', 'Organic, inorganic, physical chemistry', '🧪', '#4ECDC4'),
('Biology', 'Life sciences, anatomy, genetics, ecology', '🧬', '#45B7D1'),
('Mathematics', 'Algebra, calculus, geometry, statistics', '🔢', '#96CEB4'),
('Computer Science', 'Programming, algorithms, data structures', '💻', '#FFEAA7'),
('History', 'World history, civilizations, historical events', '📜', '#DDA0DD'),
('Geography', 'Physical and human geography, world regions', '🌍', '#98D8C8'),
('English', 'Literature, grammar, composition', '📚', '#F7DC6F'),
('General Knowledge', 'Miscellaneous topics and trivia', '🧠', '#BB8FCE'),
('Other', 'Uncategorized questions', '❓', '#85C1E9')
ON DUPLICATE KEY UPDATE `category_name` = VALUES(`category_name`);


-- ============================================================
-- Add category_id to questions table
-- ============================================================
ALTER TABLE `questions` 
ADD COLUMN IF NOT EXISTS `category_id` INT NULL AFTER `subject`,
ADD INDEX `idx_category` (`category_id`);


-- ============================================================
-- Update existing questions with category_id based on subject
-- ============================================================
UPDATE `questions` SET `category_id` = (
    SELECT `category_id` FROM `mcq_categories` WHERE `category_name` = `questions`.`subject`
) WHERE `category_id` IS NULL;


-- ============================================================
-- TABLE: mcq_performance - MCQ spaced repetition tracking
-- ============================================================
CREATE TABLE IF NOT EXISTS `mcq_performance` (
    `mcq_performance_id` INT PRIMARY KEY AUTO_INCREMENT,
    `user_id` INT NOT NULL,
    `q_id` INT NOT NULL,
    `times_attempted` INT NOT NULL DEFAULT 0,
    `times_correct` INT NOT NULL DEFAULT 0,
    `last_attempt_date` TIMESTAMP NULL,
    `next_review_date` DATE NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`user_id`) ON DELETE CASCADE,
    FOREIGN KEY (`q_id`) REFERENCES `questions`(`q_id`) ON DELETE CASCADE,
    UNIQUE KEY `unique_user_mcq` (`user_id`, `q_id`),
    INDEX `idx_user_review` (`user_id`, `next_review_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- Add points column to users table if not exists
-- ============================================================
ALTER TABLE `users` 
ADD COLUMN IF NOT EXISTS `points` INT NOT NULL DEFAULT 0 AFTER `is_admin`;


-- ============================================================
-- Add new flashcard achievements
-- ============================================================
INSERT INTO `achievements` (`achievement_code`, `title`, `description`, `icon`, `category`, `requirement_type`, `requirement_value`, `subject`) VALUES
('first_deck', 'Deck Creator', 'Create your first flashcard deck', '📁', 'flashcard', 'decks_created', 1, NULL),
('deck_collector', 'Deck Collector', 'Create 5 flashcard decks', '📚', 'flashcard', 'decks_created', 5, NULL),
('card_creator', 'Card Creator', 'Create 50 flashcards', '🃏', 'flashcard', 'cards_created', 50, NULL),
('knowledge_builder', 'Knowledge Builder', 'Create 250 flashcards', '🏗️', 'flashcard', 'cards_created', 250, NULL),
('first_study', 'First Study Session', 'Complete your first study session', '📖', 'flashcard', 'study_sessions', 1, NULL),
('study_streak_7', '7-Day Streak', 'Study for 7 days in a row', '🔥', 'streak', 'daily_streak', 7, NULL),
('study_streak_30', '30-Day Streak', 'Study for 30 days in a row', '🌟', 'streak', 'daily_streak', 30, NULL),
('point_collector_100', 'Point Collector', 'Earn 100 points', '💯', 'points', 'total_points', 100, NULL),
('point_master_1000', 'Point Master', 'Earn 1000 points', '🏆', 'points', 'total_points', 1000, NULL),
('mastered_cards_10', 'Card Master', 'Master 10 flashcards', '⭐', 'flashcard', 'cards_mastered', 10, NULL)
ON DUPLICATE KEY UPDATE `achievement_code` = VALUES(`achievement_code`);


-- ============================================================
-- Update user_statistics table for new features
-- ============================================================
ALTER TABLE `user_statistics`
ADD COLUMN IF NOT EXISTS `total_decks` INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS `total_cards` INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS `cards_mastered` INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS `flashcards_reviewed` INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS `total_points` INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS `study_sessions_count` INT DEFAULT 0;


-- ============================================================
-- VIEW: user_study_stats - Comprehensive study statistics
-- ============================================================
CREATE OR REPLACE VIEW `user_study_stats` AS
SELECT 
    u.user_id,
    u.username,
    u.points,
    COALESCE(us.total_quizzes_completed, 0) AS total_quizzes,
    COALESCE(us.total_questions_solved, 0) AS total_questions,
    COALESCE(us.current_streak_days, 0) AS current_streak,
    COALESCE(us.longest_streak_days, 0) AS longest_streak,
    COALESCE(us.total_decks, 0) AS total_decks,
    COALESCE(us.total_cards, 0) AS total_cards,
    COALESCE(us.flashcards_reviewed, 0) AS flashcards_reviewed,
    (SELECT COUNT(*) FROM decks d WHERE d.user_id = u.user_id) AS deck_count,
    (SELECT COUNT(*) FROM cards c 
     JOIN decks d ON c.deck_id = d.deck_id 
     WHERE d.user_id = u.user_id) AS card_count,
    (SELECT COUNT(*) FROM card_performance cp 
     WHERE cp.user_id = u.user_id 
     AND cp.next_review_date <= CURDATE()) AS cards_due,
    (SELECT COUNT(*) FROM user_achievements ua 
     WHERE ua.user_id = u.user_id) AS achievements_earned
FROM users u
LEFT JOIN user_statistics us ON u.user_id = us.user_id;


-- ============================================================
-- Verification
-- ============================================================
SELECT 'Flashcard migration completed successfully!' AS Status;

SHOW TABLES LIKE '%deck%';
SHOW TABLES LIKE '%card%';
SHOW TABLES LIKE '%study%';
SHOW TABLES LIKE '%mcq_cat%';
