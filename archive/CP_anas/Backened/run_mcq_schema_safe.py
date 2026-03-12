"""
Safe MCQ Schema Update - Checks for existing columns/tables before creating
"""

import mysql.connector
from mysql.connector import Error

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Root123',
    'database': 'autorevise_db'
}

def column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table"""
    cursor.execute(f"""
        SELECT COUNT(*) 
        FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA = 'autorevise_db' 
        AND TABLE_NAME = '{table_name}' 
        AND COLUMN_NAME = '{column_name}'
    """)
    result = cursor.fetchone()
    return result[0] > 0

def table_exists(cursor, table_name):
    """Check if a table exists"""
    cursor.execute(f"""
        SELECT COUNT(*) 
        FROM information_schema.TABLES 
        WHERE TABLE_SCHEMA = 'autorevise_db' 
        AND TABLE_NAME = '{table_name}'
    """)
    result = cursor.fetchone()
    return result[0] > 0

def run_safe_schema_update():
    """Execute schema updates safely"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        print("=" * 60)
        print("Safe MCQ Schema Update")
        print("=" * 60)
        print(f"Connected to database: {DB_CONFIG['database']}\n")
        
        # 1. Add is_admin column to Users table
        print("1. Checking Users.is_admin column...")
        if not column_exists(cursor, 'Users', 'is_admin'):
            print("   Adding is_admin column...")
            cursor.execute("""
                ALTER TABLE Users 
                ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT FALSE
            """)
            print("   ✅ Added is_admin column to Users table")
        else:
            print("   ✅ is_admin column already exists")
        
        # 2. Create MCQ_Questions table
        print("\n2. Checking MCQ_Questions table...")
        if not table_exists(cursor, 'MCQ_Questions'):
            print("   Creating MCQ_Questions table...")
            cursor.execute("""
                CREATE TABLE MCQ_Questions (
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
                ) ENGINE=InnoDB
            """)
            print("   ✅ Created MCQ_Questions table")
        else:
            print("   ✅ MCQ_Questions table already exists")
        
        # 3. Create MCQ_Performance table
        print("\n3. Checking MCQ_Performance table...")
        if not table_exists(cursor, 'MCQ_Performance'):
            print("   Creating MCQ_Performance table...")
            cursor.execute("""
                CREATE TABLE MCQ_Performance (
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
                ) ENGINE=InnoDB
            """)
            print("   ✅ Created MCQ_Performance table")
        else:
            print("   ✅ MCQ_Performance table already exists")
        
        # 4. Create MCQ_Upload_Log table
        print("\n4. Checking MCQ_Upload_Log table...")
        if not table_exists(cursor, 'MCQ_Upload_Log'):
            print("   Creating MCQ_Upload_Log table...")
            cursor.execute("""
                CREATE TABLE MCQ_Upload_Log (
                    upload_id INT PRIMARY KEY AUTO_INCREMENT,
                    admin_id INT NOT NULL,
                    filename VARCHAR(255) NOT NULL,
                    total_questions INT NOT NULL,
                    successful_imports INT NOT NULL,
                    failed_imports INT NOT NULL,
                    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (admin_id) REFERENCES Users(user_id) ON DELETE CASCADE
                ) ENGINE=InnoDB
            """)
            print("   ✅ Created MCQ_Upload_Log table")
        else:
            print("   ✅ MCQ_Upload_Log table already exists")
        
        # Commit all changes
        connection.commit()
        
        print("\n" + "=" * 60)
        print("✅ MCQ Schema Update Completed Successfully!")
        print("=" * 60)
        
        # Show current tables
        print("\nCurrent MCQ-related tables:")
        cursor.execute("SHOW TABLES LIKE 'MCQ%'")
        tables = cursor.fetchall()
        for table in tables:
            print(f"  - {table[0]}")
        
        # Check Users table structure
        print("\nUsers table columns:")
        cursor.execute("DESCRIBE Users")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  - {col[0]}: {col[1]}")
        
        return True
        
    except Error as e:
        print(f"\n❌ Database error: {e}")
        return False
    
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False
    
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            print("\n📊 Database connection closed.")

if __name__ == '__main__':
    success = run_safe_schema_update()
    
    if success:
        print("\n" + "=" * 60)
        print("Next Steps:")
        print("=" * 60)
        print("1. Run: python make_admin.py")
        print("2. Login as admin user")
        print("3. Access admin-mcq-upload.html")
        print("4. Upload sample_mcqs.csv")
    else:
        print("\n⚠️ Schema update failed. Please check the errors above.")
