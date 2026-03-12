"""
Make a user admin
Quick script to grant admin privileges to a user
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

def make_user_admin(user_id):
    """Grant admin privileges to a user"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # Check if user exists
        cursor.execute("SELECT user_id, username, email FROM Users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            print(f"❌ User with ID {user_id} not found!")
            return False
        
        print(f"Found user: ID={user[0]}, Username={user[1]}, Email={user[2]}")
        
        # Update user to admin
        cursor.execute("UPDATE Users SET is_admin = TRUE WHERE user_id = %s", (user_id,))
        connection.commit()
        
        print(f"✅ User {user[1]} (ID: {user_id}) is now an admin!")
        
        return True
        
    except Error as e:
        print(f"❌ Database error: {e}")
        return False
    
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

def list_all_users():
    """List all users in the database"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        cursor.execute("SELECT user_id, username, email, is_admin FROM Users")
        users = cursor.fetchall()
        
        print("\n" + "=" * 70)
        print("All Users:")
        print("=" * 70)
        print(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Admin':<10}")
        print("-" * 70)
        
        for user in users:
            is_admin = "✅ Yes" if user[3] else "❌ No"
            print(f"{user[0]:<5} {user[1]:<20} {user[2]:<30} {is_admin:<10}")
        
        print("=" * 70)
        
    except Error as e:
        print(f"❌ Database error: {e}")
    
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == '__main__':
    print("=" * 60)
    print("Make User Admin Script")
    print("=" * 60)
    
    # List all users first
    list_all_users()
    
    # Prompt for user ID
    print("\nEnter the user ID you want to make admin:")
    print("(or press Enter to make user ID 1 an admin)")
    
    user_input = input("User ID: ").strip()
    
    if user_input == '':
        user_id = 1
    else:
        try:
            user_id = int(user_input)
        except ValueError:
            print("❌ Invalid user ID. Must be a number.")
            exit(1)
    
    # Make user admin
    success = make_user_admin(user_id)
    
    if success:
        print("\n" + "=" * 60)
        print("✅ Admin setup complete!")
        print("=" * 60)
        print("You can now:")
        print("  1. Login as this user")
        print("  2. Access admin-mcq-upload.html")
        print("  3. Upload MCQ CSV files")
