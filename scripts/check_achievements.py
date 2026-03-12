"""Check if achievements table was created"""
from db_config import get_connection

conn = get_connection()
cur = conn.cursor()

print("=" * 60)
print("CHECKING ACHIEVEMENTS TABLE")
print("=" * 60)

# Check all tables
cur.execute("SHOW TABLES")
tables = [t[0] for t in cur.fetchall()]

print("\nAll tables in database:")
for t in tables:
    print(f"  ✓ {t}")

print()

# Check if user_achievements exists
if 'user_achievements' in tables:
    print("✅ user_achievements table EXISTS!")
    
    # Show structure
    cur.execute("DESCRIBE user_achievements")
    cols = cur.fetchall()
    print("\nTable structure:")
    print(f"  {'Column':<30} {'Type':<20} {'Null':<5} {'Key':<5}")
    print("  " + "-" * 60)
    for c in cols:
        print(f"  {c[0]:<30} {c[1]:<20} {c[2]:<5} {c[3]:<5}")
    
    # Check if there's any data
    cur.execute("SELECT COUNT(*) FROM user_achievements")
    count = cur.fetchone()[0]
    print(f"\n  Total records: {count}")
    
    if count > 0:
        cur.execute("SELECT * FROM user_achievements")
        achievements = cur.fetchall()
        print("\n  Achievement records:")
        for a in achievements:
            print(f"    • User {a[1]}, {a[2]}: {a[3]} quizzes, Best: {a[6]}%")
    else:
        print("\n  ⚠️  No achievement data yet")
        print("     Take a quiz to populate this table!")
else:
    print("❌ user_achievements table NOT FOUND")
    print("\nTo create it:")
    print("  1. Make sure app.py has the updated init_database() function")
    print("  2. Restart Flask: python app.py")
    print("  3. The table will be created automatically on startup")

cur.close()
conn.close()

print("\n" + "=" * 60)
