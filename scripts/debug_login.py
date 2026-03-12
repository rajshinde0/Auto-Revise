"""
Debug script to check login issues
"""
from db_config import get_connection
import bcrypt

def check_users():
    """Check all users in database"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    print("=" * 60)
    print("CHECKING USERS IN DATABASE")
    print("=" * 60)
    
    cursor.execute('SELECT user_id, username, email, full_name, is_admin, created_at FROM users')
    users = cursor.fetchall()
    
    print(f"\nTotal users: {len(users)}\n")
    
    for user in users:
        print(f"User ID: {user['user_id']}")
        print(f"  Username: {user['username']}")
        print(f"  Email: {user['email']}")
        print(f"  Full Name: {user['full_name']}")
        print(f"  Is Admin: {user['is_admin']}")
        print(f"  Created: {user['created_at']}")
        print()
    
    # Test testuser password
    print("=" * 60)
    print("TESTING TESTUSER PASSWORD")
    print("=" * 60)
    
    cursor.execute('SELECT password_hash FROM users WHERE username = %s', ('testuser',))
    result = cursor.fetchone()
    
    if result:
        stored_hash = result['password_hash']
        test_password = 'test123'
        
        print(f"\nStored hash (first 50 chars): {stored_hash[:50]}...")
        print(f"Testing password: {test_password}")
        
        # Test password
        try:
            is_valid = bcrypt.checkpw(test_password.encode('utf-8'), stored_hash.encode('utf-8'))
            print(f"Password validation result: {is_valid}")
            
            if is_valid:
                print("✅ Password is CORRECT")
            else:
                print("❌ Password is INCORRECT")
                print("\nRecreating testuser with correct password...")
                
                # Delete old testuser
                cursor.execute('DELETE FROM users WHERE username = %s', ('testuser',))
                
                # Create new testuser with correct password
                new_hash = bcrypt.hashpw(test_password.encode('utf-8'), bcrypt.gensalt())
                cursor.execute('''
                    INSERT INTO users (username, email, password_hash, full_name, is_admin, created_at)
                    VALUES (%s, %s, %s, %s, 0, NOW())
                ''', ('testuser', 'test@quiz.com', new_hash, 'Test User'))
                
                conn.commit()
                print("✅ Testuser recreated successfully")
        except Exception as e:
            print(f"❌ Error testing password: {e}")
    else:
        print("❌ Testuser not found! Creating...")
        test_password = 'test123'
        new_hash = bcrypt.hashpw(test_password.encode('utf-8'), bcrypt.gensalt())
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, full_name, is_admin, created_at)
            VALUES (%s, %s, %s, %s, 0, NOW())
        ''', ('testuser', 'test@quiz.com', new_hash, 'Test User'))
        conn.commit()
        print("✅ Testuser created successfully")
    
    # Check user_statistics
    print("\n" + "=" * 60)
    print("CHECKING USER_STATISTICS")
    print("=" * 60)
    
    cursor.execute('SELECT user_id FROM user_statistics')
    stats_users = cursor.fetchall()
    print(f"\nUsers with statistics: {len(stats_users)}")
    for su in stats_users:
        print(f"  - User ID: {su['user_id']}")
    
    # Initialize statistics for users without them
    cursor.execute('''
        INSERT IGNORE INTO user_statistics (user_id, last_quiz_date)
        SELECT user_id, CURDATE() FROM users
    ''')
    conn.commit()
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ CHECK COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    check_users()
