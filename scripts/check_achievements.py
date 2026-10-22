"""Check if achievements table was created"""
import os
import sys

# Make src/ importable so this runs from the repo root, the way the
# README documents it (python scripts/check_achievements.py).
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

from db_config import get_connection

# Windows consoles default to cp1252, which cannot encode the emoji in this
# script's progress output. Without this the script dies with
# UnicodeEncodeError instead of doing its job - and the error handler then
# fails the same way trying to report it.
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')


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
        # Select the columns explicitly. This used to be SELECT * with
        # positional indexes up to a[6] and labels describing quiz scores,
        # which matched neither this table's 5 columns (hence IndexError) nor
        # its meaning.
        cur.execute("""
            SELECT ua.user_id, u.username, a.achievement_code, a.title,
                   ua.progress_when_unlocked, ua.unlocked_at
            FROM user_achievements ua
            JOIN achievements a ON a.achievement_id = ua.achievement_id
            LEFT JOIN users u ON u.user_id = ua.user_id
            ORDER BY ua.user_id, ua.unlocked_at
        """)
        print("\n  Achievement records:")
        for user_id, username, code, title, progress, unlocked_at in cur.fetchall():
            who = username or f"user {user_id}"
            print(f"    • {who}: {title} ({code}) at {unlocked_at}, progress {progress}")
    else:
        print("\n  ⚠️  No achievement data yet")
        print("     Take a quiz to populate this table!")
else:
    print("❌ user_achievements table NOT FOUND")
    print("\nTo create it, run the migrations (see README.md):")
    print("  1. mysql -u root -p < database/COMPLETE_DATABASE_SCHEMA.sql")
    print("  2. python database/migrations/comprehensive_achievements_migration.py")
    print("  3. python database/migrations/run_flashcard_migration.py")

cur.close()
conn.close()

print("\n" + "=" * 60)
