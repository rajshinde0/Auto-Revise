"""
Comprehensive Achievements System Migration
Replaces existing simple achievements with full-featured gamification system
"""
from db_config import get_connection
from datetime import datetime

print("=" * 70)
print("   COMPREHENSIVE ACHIEVEMENTS SYSTEM MIGRATION")
print("=" * 70)

conn = get_connection()
cur = conn.cursor()

try:
    # ========== STEP 1: Backup and Drop Old Tables ==========
    print("\n📦 STEP 1: Backing up and dropping old tables...")
    
    cur.execute("DROP TABLE IF EXISTS user_achievements")
    print("   ✓ Dropped old user_achievements table")
    
    cur.execute("DROP TABLE IF EXISTS achievements")
    print("   ✓ Dropped old achievements table")
    
    cur.execute("DROP TABLE IF EXISTS user_statistics")
    print("   ✓ Dropped old user_statistics table")
    
    # ========== STEP 2: Create Enhanced Tables ==========
    print("\n🔧 STEP 2: Creating enhanced achievement tables...")
    
    # Enhanced achievements table with categories
    cur.execute("""
        CREATE TABLE achievements (
            achievement_id INT PRIMARY KEY AUTO_INCREMENT,
            achievement_code VARCHAR(100) UNIQUE NOT NULL,
            title VARCHAR(150) NOT NULL,
            description TEXT,
            icon VARCHAR(20) DEFAULT '🏆',
            category VARCHAR(50) NOT NULL,
            requirement_type VARCHAR(50) NOT NULL,
            requirement_value INT,
            subject VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_category (category),
            INDEX idx_code (achievement_code)
        )
    """)
    print("   ✓ Created enhanced achievements table")
    
    # User achievements with metadata
    cur.execute("""
        CREATE TABLE user_achievements (
            id INT PRIMARY KEY AUTO_INCREMENT,
            user_id INT NOT NULL,
            achievement_id INT NOT NULL,
            unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            progress_when_unlocked INT DEFAULT 100,
            UNIQUE KEY unique_user_achievement (user_id, achievement_id),
            INDEX idx_user_id (user_id),
            INDEX idx_achievement_id (achievement_id),
            INDEX idx_unlocked_at (unlocked_at),
            FOREIGN KEY (achievement_id) REFERENCES achievements(achievement_id) ON DELETE CASCADE
        )
    """)
    print("   ✓ Created user_achievements tracking table")
    
    # Comprehensive user statistics table
    cur.execute("""
        CREATE TABLE user_statistics (
            id INT PRIMARY KEY AUTO_INCREMENT,
            user_id INT NOT NULL UNIQUE,
            
            -- Quiz completion tracking
            total_quizzes_completed INT DEFAULT 0,
            total_questions_solved INT DEFAULT 0,
            total_correct_answers INT DEFAULT 0,
            
            -- Subject-specific tracking
            physics_quizzes INT DEFAULT 0,
            chemistry_quizzes INT DEFAULT 0,
            biology_quizzes INT DEFAULT 0,
            mathematics_quizzes INT DEFAULT 0,
            
            -- Perfect score tracking
            perfect_quizzes_count INT DEFAULT 0,
            physics_perfect_count INT DEFAULT 0,
            chemistry_perfect_count INT DEFAULT 0,
            biology_perfect_count INT DEFAULT 0,
            mathematics_perfect_count INT DEFAULT 0,
            
            -- First quiz completion flags
            physics_completed BOOLEAN DEFAULT FALSE,
            chemistry_completed BOOLEAN DEFAULT FALSE,
            biology_completed BOOLEAN DEFAULT FALSE,
            mathematics_completed BOOLEAN DEFAULT FALSE,
            
            -- Streak tracking
            current_streak_days INT DEFAULT 0,
            longest_streak_days INT DEFAULT 0,
            last_quiz_date DATE,
            
            -- Consecutive perfect scores
            consecutive_perfect_quizzes INT DEFAULT 0,
            consecutive_correct_answers INT DEFAULT 0,
            max_consecutive_correct INT DEFAULT 0,
            
            -- Time-based achievements
            night_owl_count INT DEFAULT 0,
            early_bird_count INT DEFAULT 0,
            
            -- Review tracking
            total_reviews INT DEFAULT 0,
            incorrect_answers_reviewed INT DEFAULT 0,
            
            -- Other
            quiz_retakes JSON,  -- Store {result_id: [scores]} for retry tracking
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_user_id (user_id),
            INDEX idx_last_quiz_date (last_quiz_date)
        )
    """)
    print("   ✓ Created comprehensive user_statistics table")
    
    # Quiz session tracking for streaks and time-based achievements
    cur.execute("""
        CREATE TABLE IF NOT EXISTS quiz_sessions (
            session_id INT PRIMARY KEY AUTO_INCREMENT,
            user_id INT NOT NULL,
            result_id INT NOT NULL,
            subject VARCHAR(50) NOT NULL,
            start_time DATETIME NOT NULL,
            end_time DATETIME NOT NULL,
            duration_seconds INT NOT NULL,
            avg_time_per_question DECIMAL(10,2),
            time_of_day VARCHAR(20),
            quiz_date DATE NOT NULL,
            INDEX idx_user_id (user_id),
            INDEX idx_quiz_date (quiz_date),
            INDEX idx_result_id (result_id),
            FOREIGN KEY (result_id) REFERENCES results(result_id) ON DELETE CASCADE
        )
    """)
    print("   ✓ Created quiz_sessions tracking table")
    
    conn.commit()
    
    # ========== STEP 3: Insert Comprehensive Achievement Definitions ==========
    print("\n🏆 STEP 3: Inserting comprehensive achievement definitions...")
    
    achievements_data = [
        # ===== MILESTONE ACHIEVEMENTS =====
        ('quiz_rookie', 'Quiz Rookie', 'Complete your first quiz', '🎯', 'milestone', 'total_quizzes', 1, None),
        ('quiz_enthusiast', 'Quiz Enthusiast', 'Complete 10 quizzes total', '📚', 'milestone', 'total_quizzes', 10, None),
        ('quiz_pro', 'Quiz Pro', 'Complete 50 quizzes total', '🎓', 'milestone', 'total_quizzes', 50, None),
        ('quiz_legend', 'Quiz Legend', 'Complete 100 quizzes total', '👑', 'milestone', 'total_quizzes', 100, None),
        
        ('knowledge_seeker', 'Knowledge Seeker', 'Attempt 200 total questions', '🧠', 'milestone', 'total_questions', 200, None),
        
        # ===== SUBJECT-BASED ACHIEVEMENTS =====
        ('first_steps', 'First Steps', 'Complete your first quiz in any subject', '🏁', 'subject', 'first_quiz_any', 1, None),
        
        ('physics_starter', 'Physics Starter', 'Complete your first Physics quiz', '⚛️', 'subject', 'first_quiz_subject', 1, 'Physics'),
        ('chemistry_starter', 'Chemistry Starter', 'Complete your first Chemistry quiz', '🧪', 'subject', 'first_quiz_subject', 1, 'Chemistry'),
        ('biology_starter', 'Biology Starter', 'Complete your first Biology quiz', '🧬', 'subject', 'first_quiz_subject', 1, 'Biology'),
        ('mathematics_starter', 'Mathematics Starter', 'Complete your first Mathematics quiz', '🔢', 'subject', 'first_quiz_subject', 1, 'Mathematics'),
        
        ('all_rounder', 'All-Rounder', 'Complete one quiz in every subject', '🌍', 'subject', 'all_subjects_once', 4, None),
        
        ('subject_lover', 'Subject Lover', 'Take 10 quizzes in one subject', '❤️', 'subject', 'subject_dedication', 10, None),
        
        # ===== PERFECT SCORE ACHIEVEMENTS =====
        ('flawless_victory', 'Flawless Victory', 'Score 100% in any quiz', '🥇', 'perfect', 'perfect_once', 1, None),
        ('perfectionist', 'Perfectionist', 'Score 100% in all subjects at least once', '🌟', 'perfect', 'perfect_all_subjects', 4, None),
        ('precision_player', 'Precision Player', 'Score 90% or above in 5 consecutive quizzes', '🎯', 'perfect', 'consecutive_90_plus', 5, None),
        
        # ===== ACCURACY ACHIEVEMENTS =====
        ('sharp_shooter', 'Sharp Shooter', 'Get 10 correct answers consecutively', '🏹', 'accuracy', 'consecutive_correct', 10, None),
        
        # ===== TIME-BASED ACHIEVEMENTS =====
        ('fast_thinker', 'Fast Thinker', 'Complete a quiz in under 1 minute per question', '⚡', 'time', 'fast_completion', 60, None),
        ('night_owl', 'Night Owl', 'Finish a quiz between 12 AM and 5 AM', '🦉', 'time', 'night_quiz', 1, None),
        ('early_bird', 'Early Bird', 'Finish a quiz before 8 AM', '🐦', 'time', 'early_quiz', 1, None),
        
        # ===== STREAK ACHIEVEMENTS =====
        ('steady_learner', 'Steady Learner', 'Attempt quizzes for 3 consecutive days', '📅', 'streak', 'daily_streak', 3, None),
        ('consistency_streak', 'Consistency Streak', 'Take quizzes for 7 days in a row', '🔥', 'streak', 'daily_streak', 7, None),
        
        # ===== IMPROVEMENT ACHIEVEMENTS =====
        ('comeback_kid', 'Comeback Kid', 'Improve by ≥20% from previous quiz in same subject', '📈', 'improvement', 'score_improvement', 20, None),
        ('retry_champion', 'Retry Champion', 'Retake the same quiz 3+ times and improve score', '🔄', 'improvement', 'quiz_retries', 3, None),
        
        # ===== REVIEW & LEARNING ACHIEVEMENTS =====
        ('error_learner', 'Error Learner', 'Review 50 incorrect answers total', '📖', 'review', 'review_mistakes', 50, None),
        
        # ===== SESSION ACHIEVEMENTS =====
        ('marathon_session', 'Marathon Session', 'Complete 5 quizzes in one sitting', '🏃', 'session', 'quiz_marathon', 5, None),
    ]
    
    cur.executemany("""
        INSERT INTO achievements (achievement_code, title, description, icon, category, requirement_type, requirement_value, subject)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, achievements_data)
    
    print(f"   ✓ Inserted {len(achievements_data)} achievement definitions")
    print(f"   ✓ Categories: Milestone, Subject, Perfect, Accuracy, Time, Streak, Improvement, Review, Session")
    
    conn.commit()
    
    # ========== STEP 4: Verification ==========
    print("\n✅ STEP 4: Verifying migration...")
    
    cur.execute("SELECT COUNT(*) FROM achievements")
    achievement_count = cur.fetchone()[0]
    print(f"   ✓ Total achievements: {achievement_count}")
    
    cur.execute("SELECT category, COUNT(*) FROM achievements GROUP BY category")
    categories = cur.fetchall()
    for cat, count in categories:
        print(f"   ✓ {cat.capitalize()}: {count} achievements")
    
    print("\n" + "=" * 70)
    print("   ✅ MIGRATION COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    print("\n📋 Summary:")
    print(f"   • {achievement_count} comprehensive achievements created")
    print("   • Enhanced tracking for streaks, time, and improvements")
    print("   • Quiz session tracking for time-based achievements")
    print("   • Ready for full gamification experience")
    print("\n🚀 Next step: Run 'python app.py' to start the application")
    
except Exception as e:
    print(f"\n❌ Error during migration: {e}")
    import traceback
    traceback.print_exc()
    conn.rollback()
finally:
    cur.close()
    conn.close()
