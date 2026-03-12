"""
Migration script to add Retry Champion achievement
Adds the 26th achievement: Retry Champion - for users who retake quizzes and improve
"""

from db_config import get_connection

def add_retry_champion_achievement():
    """Add Retry Champion achievement to database"""
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        print("=" * 60)
        print("ADDING RETRY CHAMPION ACHIEVEMENT")
        print("=" * 60)
        
        # Step 1: Check if quiz_retakes column exists
        print("\n✓ STEP 1: Checking quiz_retakes column...")
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'user_statistics' 
            AND COLUMN_NAME = 'quiz_retakes'
        """)
        
        if not cursor.fetchone():
            print("  Adding quiz_retakes column to user_statistics table...")
            cursor.execute("""
                ALTER TABLE user_statistics 
                ADD COLUMN quiz_retakes JSON COMMENT 'Tracks quiz retakes: {subject: {result_id: count}}'
            """)
            conn.commit()
            print("  ✓ quiz_retakes column added")
        else:
            print("  ✓ quiz_retakes column already exists")
        
        # Step 2: Add Retry Champion achievement
        print("\n✓ STEP 2: Adding Retry Champion achievement...")
        cursor.execute("""
            SELECT achievement_id FROM achievements 
            WHERE achievement_code = 'retry_champion'
        """)
        
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO achievements (
                    title, description, icon, achievement_code, category
                )
                VALUES (
                    'Retry Champion',
                    'Retake same subject 5+ times with consistent improvement',
                    '🔄',
                    'retry_champion',
                    'improvement'
                )
            """)
            conn.commit()
            print("  ✓ Retry Champion achievement added")
        else:
            print("  ✓ Retry Champion achievement already exists")
        
        # Step 3: Initialize quiz_retakes for existing users
        print("\n✓ STEP 3: Initializing quiz_retakes for existing users...")
        cursor.execute("""
            UPDATE user_statistics 
            SET quiz_retakes = JSON_OBJECT()
            WHERE quiz_retakes IS NULL
        """)
        conn.commit()
        print(f"  ✓ Initialized quiz_retakes for {cursor.rowcount} users")
        
        # Step 4: Verification
        print("\n✓ STEP 4: Verification...")
        cursor.execute("SELECT COUNT(*) FROM achievements WHERE achievement_code = 'retry_champion'")
        achievement_count = cursor.fetchone()[0]
        print(f"  ✓ Retry Champion achievements in database: {achievement_count}")
        
        cursor.execute("SELECT COUNT(*) FROM user_statistics WHERE quiz_retakes IS NOT NULL")
        users_with_retakes = cursor.fetchone()[0]
        print(f"  ✓ Users with quiz_retakes initialized: {users_with_retakes}")
        
        print("\n" + "=" * 60)
        print("✅ RETRY CHAMPION ACHIEVEMENT MIGRATION COMPLETED!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    add_retry_champion_achievement()
