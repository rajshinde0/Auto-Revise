"""
Safe database schema updater for MCQ Categories feature
Checks for existing columns/tables before creating them
"""

import mysql.connector
from mysql.connector import Error

# Database configuration (match your App1.py settings)
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Root123',
    'database': 'autorevise_db'
}

def get_connection():
    """Create and return a database connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            print("✓ Connected to MySQL database")
            return connection
    except Error as e:
        print(f"✗ Error connecting to MySQL: {e}")
        return None

def table_exists(cursor, table_name):
    """Check if a table exists"""
    cursor.execute(f"""
        SELECT COUNT(*) 
        FROM information_schema.tables 
        WHERE table_schema = '{DB_CONFIG['database']}' 
        AND table_name = '{table_name}'
    """)
    return cursor.fetchone()[0] > 0

def column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table"""
    cursor.execute(f"""
        SELECT COUNT(*) 
        FROM information_schema.columns 
        WHERE table_schema = '{DB_CONFIG['database']}' 
        AND table_name = '{table_name}' 
        AND column_name = '{column_name}'
    """)
    return cursor.fetchone()[0] > 0

def safe_execute(cursor, sql, description):
    """Execute SQL with error handling"""
    try:
        cursor.execute(sql)
        print(f"✓ {description}")
        return True
    except Error as e:
        print(f"✗ {description} - Error: {e}")
        return False

def main():
    """Main function to safely update schema"""
    connection = get_connection()
    if not connection:
        return
    
    try:
        cursor = connection.cursor()
        
        print("\n" + "="*60)
        print("MCQ CATEGORIES SCHEMA UPDATE")
        print("="*60)
        
        # 1. Create MCQ_Categories table
        print("\n[1] Creating MCQ_Categories table...")
        if not table_exists(cursor, 'MCQ_Categories'):
            create_categories_table = """
            CREATE TABLE MCQ_Categories (
                category_id INT PRIMARY KEY AUTO_INCREMENT,
                category_name VARCHAR(100) NOT NULL UNIQUE,
                description TEXT NULL,
                icon VARCHAR(50) NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_category_name (category_name)
            ) ENGINE=InnoDB;
            """
            safe_execute(cursor, create_categories_table, "Created MCQ_Categories table")
            connection.commit()
        else:
            print("⊙ MCQ_Categories table already exists")
        
        # 2. Add category_id column to MCQ_Questions
        print("\n[2] Adding category_id to MCQ_Questions...")
        if table_exists(cursor, 'MCQ_Questions'):
            if not column_exists(cursor, 'MCQ_Questions', 'category_id'):
                add_category_column = """
                ALTER TABLE MCQ_Questions 
                ADD COLUMN category_id INT NULL AFTER deck_id
                """
                safe_execute(cursor, add_category_column, "Added category_id column")
                connection.commit()
                
                # Add foreign key
                add_fk = """
                ALTER TABLE MCQ_Questions 
                ADD FOREIGN KEY (category_id) REFERENCES MCQ_Categories(category_id) ON DELETE SET NULL
                """
                safe_execute(cursor, add_fk, "Added foreign key constraint")
                connection.commit()
                
                # Add index
                add_index = """
                ALTER TABLE MCQ_Questions 
                ADD INDEX idx_category (category_id)
                """
                safe_execute(cursor, add_index, "Added category index")
                connection.commit()
            else:
                print("⊙ category_id column already exists in MCQ_Questions")
        else:
            print("⊙ MCQ_Questions table doesn't exist yet")
        
        # 3. Insert default categories
        print("\n[3] Inserting default categories...")
        categories = [
            ('Biology', 'Life sciences, anatomy, genetics, ecology', 'fa-microscope'),
            ('Physics', 'Mechanics, thermodynamics, electromagnetism, optics', 'fa-atom'),
            ('Chemistry', 'Organic, inorganic, physical chemistry', 'fa-flask'),
            ('Mathematics', 'Algebra, calculus, geometry, statistics', 'fa-calculator'),
            ('Computer Science', 'Programming, algorithms, data structures', 'fa-laptop-code'),
            ('History', 'World history, civilizations, historical events', 'fa-landmark'),
            ('Geography', 'Physical and human geography, world regions', 'fa-globe-americas'),
            ('English', 'Literature, grammar, composition', 'fa-book'),
            ('General Knowledge', 'Miscellaneous topics and trivia', 'fa-brain'),
            ('Other', 'Uncategorized questions', 'fa-question-circle')
        ]
        
        insert_query = """
        INSERT INTO MCQ_Categories (category_name, description, icon) 
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE category_name=category_name
        """
        
        for category in categories:
            try:
                cursor.execute(insert_query, category)
                print(f"  ✓ Added/Updated category: {category[0]}")
            except Error as e:
                print(f"  ⊙ Category {category[0]}: {e}")
        
        connection.commit()
        
        # 4. Add category_id to MCQ_Upload_Log
        print("\n[4] Updating MCQ_Upload_Log table...")
        if table_exists(cursor, 'MCQ_Upload_Log'):
            if not column_exists(cursor, 'MCQ_Upload_Log', 'category_id'):
                add_log_category = """
                ALTER TABLE MCQ_Upload_Log 
                ADD COLUMN category_id INT NULL AFTER filename
                """
                safe_execute(cursor, add_log_category, "Added category_id to MCQ_Upload_Log")
                connection.commit()
                
                add_log_fk = """
                ALTER TABLE MCQ_Upload_Log 
                ADD FOREIGN KEY (category_id) REFERENCES MCQ_Categories(category_id) ON DELETE SET NULL
                """
                safe_execute(cursor, add_log_fk, "Added foreign key to MCQ_Upload_Log")
                connection.commit()
            else:
                print("⊙ category_id column already exists in MCQ_Upload_Log")
        else:
            print("⊙ MCQ_Upload_Log table doesn't exist yet")
        
        # 5. Verification
        print("\n" + "="*60)
        print("VERIFICATION")
        print("="*60)
        
        cursor.execute("SELECT COUNT(*) FROM MCQ_Categories")
        count = cursor.fetchone()[0]
        print(f"✓ Total categories in database: {count}")
        
        cursor.execute("SELECT category_name FROM MCQ_Categories ORDER BY category_name")
        categories = cursor.fetchall()
        print("\nAvailable categories:")
        for cat in categories:
            print(f"  • {cat[0]}")
        
        print("\n" + "="*60)
        print("✓ MCQ CATEGORIES SCHEMA UPDATE COMPLETE!")
        print("="*60)
        
    except Error as e:
        print(f"\n✗ An error occurred: {e}")
        connection.rollback()
    
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("\n✓ Database connection closed")

if __name__ == "__main__":
    main()
