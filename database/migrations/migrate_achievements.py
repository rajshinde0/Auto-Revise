"""
Migration script to upgrade to new achievements system
This will drop old tables and create new ones
"""
from db_config import get_connection

print("=" * 60)
print("MIGRATING TO NEW ACHIEVEMENTS SYSTEM")
print("=" * 60)

conn = get_connection()
cur = conn.cursor()

try:
    # Drop old tables
    print("\n1. Dropping old tables...")
    cur.execute("DROP TABLE IF EXISTS user_achievements")
    print("   ✓ Dropped old user_achievements table")
    
    cur.execute("DROP TABLE IF EXISTS achievements")
    print("   ✓ Dropped old achievements table (if exists)")
    
    cur.execute("DROP TABLE IF EXISTS user_statistics")
    print("   ✓ Dropped old user_statistics table")
    
    # Create new achievements table
    print("\n2. Creating new achievements table...")
    cur.execute("""
        CREATE TABLE achievements (
            achievement_id INT PRIMARY KEY AUTO_INCREMENT,
            achievement_code VARCHAR(50) UNIQUE NOT NULL,
            title VARCHAR(100) NOT NULL,
            description TEXT,
            icon VARCHAR(10),
            requirement_type VARCHAR(50),
            requirement_value INT,
            subject VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("   ✓ Created achievements table")
    
    # Create new user_achievements tracking table
    print("\n3. Creating user_achievements tracking table...")
    cur.execute("""
        CREATE TABLE user_achievements (
            id INT PRIMARY KEY AUTO_INCREMENT,
            user_id INT NOT NULL,
            achievement_id INT NOT NULL,
            unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY unique_user_achievement (user_id, achievement_id),
            INDEX idx_user_id (user_id),
            INDEX idx_achievement_id (achievement_id),
            FOREIGN KEY (achievement_id) REFERENCES achievements(achievement_id)
        )
    """)
    print("   ✓ Created user_achievements table")
    
    # Create user statistics table
    print("\n4. Creating user_statistics table...")
    cur.execute("""
        CREATE TABLE user_statistics (
            id INT PRIMARY KEY AUTO_INCREMENT,
            user_id INT NOT NULL,
            total_questions_solved INT DEFAULT 0,
            perfect_quizzes_count INT DEFAULT 0,
            physics_100_count INT DEFAULT 0,
            chemistry_100_count INT DEFAULT 0,
            biology_100_count INT DEFAULT 0,
            mathematics_100_count INT DEFAULT 0,
            physics_completed BOOLEAN DEFAULT FALSE,
            chemistry_completed BOOLEAN DEFAULT FALSE,
            biology_completed BOOLEAN DEFAULT FALSE,
            mathematics_completed BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY unique_user (user_id)
        )
    """)
    print("   ✓ Created user_statistics table")
    
    # Insert achievement definitions
    print("\n5. Inserting achievement definitions...")
    achievements_data = [
        ('first_quiz_physics', '🏁 Physics Pioneer', 'Complete your first Physics quiz', '🏁', 'first_quiz', 1, 'Physics'),
        ('first_quiz_chemistry', '🏁 Chemistry Champion', 'Complete your first Chemistry quiz', '🏁', 'first_quiz', 1, 'Chemistry'),
        ('first_quiz_biology', '🏁 Biology Beginner', 'Complete your first Biology quiz', '🏁', 'first_quiz', 1, 'Biology'),
        ('first_quiz_mathematics', '🏁 Math Master Start', 'Complete your first Mathematics quiz', '🏁', 'first_quiz', 1, 'Mathematics'),
        ('10_questions', '🔟 Quick Learner', 'Solve 10 total questions', '🔟', 'questions_solved', 10, None),
        ('50_questions', '💯 Knowledge Seeker', 'Solve 50 total questions', '💯', 'questions_solved', 50, None),
        ('100_questions', '🧠 Brain Power', 'Solve 100 total questions', '🧠', 'questions_solved', 100, None),
        ('perfect_quiz', '🥇 Perfect Score', 'Score 100% on any quiz', '🥇', 'perfect_quiz', 1, None),
        ('subject_master', '🌟 Ultimate Master', 'Score 100% in all four subjects', '🌟', 'all_subjects_perfect', 4, None)
    ]
    
    cur.executemany("""
        INSERT INTO achievements (achievement_code, title, description, icon, requirement_type, requirement_value, subject)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, achievements_data)
    print(f"   ✓ Inserted {len(achievements_data)} achievement definitions")
    
    conn.commit()
    
    print("\n" + "=" * 60)
    print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("\nNew tables created:")
    print("  • achievements (9 achievement definitions)")
    print("  • user_achievements (tracks unlocked achievements)")
    print("  • user_statistics (tracks user progress)")
    print("\nYou can now run: python app.py")
    
except Exception as e:
    print(f"\n❌ Error during migration: {e}")
    conn.rollback()
finally:
    cur.close()
    conn.close()
