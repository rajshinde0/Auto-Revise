"""
Run Flashcard Migration Script
Executes the flashcard_migration.sql to add new tables
"""

from db_config import get_connection

def run_migration():
    conn = get_connection()
    cursor = conn.cursor()
    
    print("Starting flashcard migration...")
    
    # Create decks table
    print("Creating decks table...", end=" ")
    cursor.execute("""
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
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    print("OK")
    
    # Create cards table
    print("Creating cards table...", end=" ")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS `cards` (
            `card_id` INT PRIMARY KEY AUTO_INCREMENT,
            `deck_id` INT NOT NULL,
            `front_content` TEXT NOT NULL,
            `back_content` TEXT NOT NULL,
            `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (`deck_id`) REFERENCES `decks`(`deck_id`) ON DELETE CASCADE,
            INDEX `idx_deck_id` (`deck_id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    print("OK")
    
    # Create card_performance table (SM-2 tracking)
    print("Creating card_performance table...", end=" ")
    cursor.execute("""
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
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    print("OK")
    
    # Create study_log table
    print("Creating study_log table...", end=" ")
    cursor.execute("""
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
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    print("OK")
    
    # Create mcq_categories table
    print("Creating mcq_categories table...", end=" ")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS `mcq_categories` (
            `category_id` INT PRIMARY KEY AUTO_INCREMENT,
            `category_name` VARCHAR(100) NOT NULL UNIQUE,
            `description` TEXT NULL,
            `icon` VARCHAR(50) NULL,
            `color` VARCHAR(20) DEFAULT '#667eea',
            `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX `idx_category_name` (`category_name`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    print("OK")
    
    # Insert default categories
    print("Inserting default MCQ categories...", end=" ")
    categories = [
        ('Physics', 'Mechanics, thermodynamics, electromagnetism, optics', 'atom', '#FF6B6B'),
        ('Chemistry', 'Organic, inorganic, physical chemistry', 'flask', '#4ECDC4'),
        ('Biology', 'Life sciences, anatomy, genetics, ecology', 'dna', '#45B7D1'),
        ('Mathematics', 'Algebra, calculus, geometry, statistics', 'calculator', '#96CEB4'),
        ('Computer Science', 'Programming, algorithms, data structures', 'laptop-code', '#FFEAA7'),
        ('History', 'World history, civilizations, historical events', 'landmark', '#DDA0DD'),
        ('Geography', 'Physical and human geography, world regions', 'globe-americas', '#98D8C8'),
        ('English', 'Literature, grammar, composition', 'book', '#F7DC6F'),
        ('General Knowledge', 'Miscellaneous topics and trivia', 'brain', '#BB8FCE'),
        ('Other', 'Uncategorized questions', 'question-circle', '#85C1E9')
    ]
    for cat in categories:
        try:
            cursor.execute("""
                INSERT INTO mcq_categories (category_name, description, icon, color)
                VALUES (%s, %s, %s, %s)
            """, cat)
        except:
            pass  # Ignore duplicates
    print("OK")
    
    # Create mcq_performance table
    print("Creating mcq_performance table...", end=" ")
    cursor.execute("""
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
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    print("OK")
    
    # Add points column to users if not exists
    print("Adding points column to users...", end=" ")
    try:
        cursor.execute("ALTER TABLE `users` ADD COLUMN `points` INT NOT NULL DEFAULT 0 AFTER `is_admin`")
        print("OK")
    except Exception as e:
        if 'Duplicate column' in str(e):
            print("Already exists")
        else:
            print(f"Skipped: {e}")
    
    # Add category_id to questions if not exists
    print("Adding category_id to questions...", end=" ")
    try:
        cursor.execute("ALTER TABLE `questions` ADD COLUMN `category_id` INT NULL AFTER `subject`")
        cursor.execute("ALTER TABLE `questions` ADD INDEX `idx_category` (`category_id`)")
        print("OK")
    except Exception as e:
        if 'Duplicate column' in str(e) or 'Duplicate key' in str(e):
            print("Already exists")
        else:
            print(f"Skipped: {e}")
    
    # Update questions with category_id based on subject
    print("Updating questions with category_id...", end=" ")
    cursor.execute("""
        UPDATE questions q
        SET q.category_id = (
            SELECT c.category_id FROM mcq_categories c 
            WHERE LOWER(c.category_name) = LOWER(q.subject)
            LIMIT 1
        )
        WHERE q.category_id IS NULL
    """)
    print(f"OK ({cursor.rowcount} rows)")
    
    # Add new columns to user_statistics
    print("Updating user_statistics table...", end=" ")
    columns_to_add = [
        ('total_decks', 'INT DEFAULT 0'),
        ('total_cards', 'INT DEFAULT 0'),
        ('cards_mastered', 'INT DEFAULT 0'),
        ('flashcards_reviewed', 'INT DEFAULT 0'),
        ('total_points', 'INT DEFAULT 0'),
        ('study_sessions_count', 'INT DEFAULT 0')
    ]
    for col_name, col_type in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE `user_statistics` ADD COLUMN `{col_name}` {col_type}")
        except:
            pass  # Column already exists
    print("OK")
    
    # Add new flashcard achievements
    print("Adding flashcard achievements...", end=" ")
    achievements = [
        ('first_deck', 'Deck Creator', 'Create your first flashcard deck', 'folder', 'flashcard', 'decks_created', 1, None),
        ('deck_collector', 'Deck Collector', 'Create 5 flashcard decks', 'folder-open', 'flashcard', 'decks_created', 5, None),
        ('card_creator', 'Card Creator', 'Create 50 flashcards', 'clone', 'flashcard', 'cards_created', 50, None),
        ('knowledge_builder', 'Knowledge Builder', 'Create 250 flashcards', 'cubes', 'flashcard', 'cards_created', 250, None),
        ('first_study', 'First Study Session', 'Complete your first study session', 'book-open', 'flashcard', 'study_sessions', 1, None),
        ('study_streak_7', '7-Day Streak', 'Study for 7 days in a row', 'fire', 'streak', 'daily_streak', 7, None),
        ('study_streak_30', '30-Day Streak', 'Study for 30 days in a row', 'star', 'streak', 'daily_streak', 30, None),
        ('point_collector_100', 'Point Collector', 'Earn 100 points', 'coins', 'points', 'total_points', 100, None),
        ('point_master_1000', 'Point Master', 'Earn 1000 points', 'trophy', 'points', 'total_points', 1000, None),
        ('mastered_cards_10', 'Card Master', 'Master 10 flashcards', 'award', 'flashcard', 'cards_mastered', 10, None)
    ]
    for ach in achievements:
        try:
            cursor.execute("""
                INSERT INTO achievements (achievement_code, title, description, icon, category, requirement_type, requirement_value, subject)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, ach)
        except:
            pass  # Ignore duplicates
    print("OK")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("\n" + "="*50)
    print("MIGRATION COMPLETED SUCCESSFULLY!")
    print("="*50)

if __name__ == '__main__':
    run_migration()
