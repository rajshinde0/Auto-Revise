"""
Database migration to add user authentication system
Adds users table and updates existing tables for multi-user support
"""
from db_config import get_connection
import bcrypt

print("=" * 70)
print("   USER AUTHENTICATION SYSTEM MIGRATION")
print("=" * 70)

conn = get_connection()
cur = conn.cursor()

try:
    # ========== STEP 1: Create Users Table ==========
    print("\n📦 STEP 1: Creating users table...")
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INT PRIMARY KEY AUTO_INCREMENT,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            full_name VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP NULL,
            is_active BOOLEAN DEFAULT TRUE,
            is_admin BOOLEAN DEFAULT FALSE,
            INDEX idx_username (username),
            INDEX idx_email (email)
        )
    """)
    print("   ✓ Created users table")
    
    # ========== STEP 2: Create default admin user ==========
    print("\n👤 STEP 2: Creating default users...")
    
    # Check if admin already exists
    cur.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
    if cur.fetchone()[0] == 0:
        # Create admin user (password: admin123)
        admin_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt())
        cur.execute("""
            INSERT INTO users (username, email, password_hash, full_name, is_admin)
            VALUES (%s, %s, %s, %s, %s)
        """, ('admin', 'admin@quiz.com', admin_hash.decode('utf-8'), 'Administrator', True))
        print("   ✓ Created admin user (username: admin, password: admin123)")
    
    # Check if default test user exists
    cur.execute("SELECT COUNT(*) FROM users WHERE user_id = 1")
    if cur.fetchone()[0] == 0:
        # Create default test user (password: test123)
        test_hash = bcrypt.hashpw('test123'.encode('utf-8'), bcrypt.gensalt())
        cur.execute("""
            INSERT INTO users (user_id, username, email, password_hash, full_name)
            VALUES (%s, %s, %s, %s, %s)
        """, (1, 'testuser', 'test@quiz.com', test_hash.decode('utf-8'), 'Test User'))
        print("   ✓ Created test user (username: testuser, password: test123)")
    else:
        print("   ✓ Default user (user_id=1) already exists")
    
    # ========== STEP 3: Add foreign keys to existing tables ==========
    print("\n🔗 STEP 3: Adding foreign key constraints...")
    
    # Check if results table has foreign key
    cur.execute("""
        SELECT COUNT(*) 
        FROM information_schema.TABLE_CONSTRAINTS 
        WHERE CONSTRAINT_SCHEMA = DATABASE()
        AND TABLE_NAME = 'results'
        AND CONSTRAINT_TYPE = 'FOREIGN KEY'
        AND CONSTRAINT_NAME = 'fk_results_user'
    """)
    
    if cur.fetchone()[0] == 0:
        try:
            cur.execute("""
                ALTER TABLE results
                ADD CONSTRAINT fk_results_user
                FOREIGN KEY (user_id) REFERENCES users(user_id)
                ON DELETE CASCADE
            """)
            print("   ✓ Added foreign key to results table")
        except Exception as e:
            print(f"   ⚠️ Foreign key may already exist: {e}")
    else:
        print("   ✓ Foreign key already exists on results table")
    
    # ========== STEP 4: Create sessions table for security ==========
    print("\n🔐 STEP 4: Creating sessions table...")
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_sessions (
            session_id VARCHAR(255) PRIMARY KEY,
            user_id INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            ip_address VARCHAR(45),
            user_agent TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            INDEX idx_user_id (user_id),
            INDEX idx_expires_at (expires_at)
        )
    """)
    print("   ✓ Created user_sessions table")
    
    # ========== STEP 5: Create login_attempts for rate limiting ==========
    print("\n🛡️ STEP 5: Creating login_attempts table for rate limiting...")
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS login_attempts (
            id INT PRIMARY KEY AUTO_INCREMENT,
            username VARCHAR(50) NOT NULL,
            ip_address VARCHAR(45) NOT NULL,
            attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            success BOOLEAN DEFAULT FALSE,
            INDEX idx_username_time (username, attempted_at),
            INDEX idx_ip_time (ip_address, attempted_at)
        )
    """)
    print("   ✓ Created login_attempts table")
    
    conn.commit()
    
    # ========== STEP 6: Verification ==========
    print("\n✅ STEP 6: Verifying migration...")
    
    cur.execute("SELECT COUNT(*) FROM users")
    user_count = cur.fetchone()[0]
    print(f"   ✓ Total users: {user_count}")
    
    cur.execute("SELECT username, email, is_admin FROM users")
    users = cur.fetchall()
    for user in users:
        role = "Admin" if user[2] else "User"
        print(f"   ✓ {user[0]} ({user[1]}) - {role}")
    
    print("\n" + "=" * 70)
    print("   ✅ AUTHENTICATION MIGRATION COMPLETED!")
    print("=" * 70)
    print("\n📋 Default Credentials:")
    print("   Admin:    username='admin',    password='admin123'")
    print("   Test User: username='testuser', password='test123'")
    print("\n🔒 Security Features Added:")
    print("   • Bcrypt password hashing")
    print("   • Session management table")
    print("   • Login attempt tracking (rate limiting)")
    print("   • Foreign key constraints")
    print("\n🚀 Next step: Restart Flask app to use new authentication")
    
except Exception as e:
    print(f"\n❌ Error during migration: {e}")
    import traceback
    traceback.print_exc()
    conn.rollback()
finally:
    cur.close()
    conn.close()
