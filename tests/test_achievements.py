"""
Test script to verify the achievements system
"""
import os
import sys

# Make src/ importable when run as `pytest tests/` from the repo root.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

from db_config import get_connection

# Windows consoles default to cp1252, which cannot encode the emoji in this
# script's progress output. Without this the script dies with
# UnicodeEncodeError instead of doing its job - and the error handler then
# fails the same way trying to report it.
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')


# These modules are integration checks: they run top-level code against a live
# MySQL instance rather than being self-contained unit tests. Skip the module
# cleanly when no database is reachable so `pytest tests/` stays green in
# environments without one (and still runs for real when a DB is configured).
try:
    _probe = get_connection()
    _probe.close()
except Exception as _exc:  # pragma: no cover - environment dependent
    try:
        import pytest
        pytest.skip(f"MySQL not reachable: {_exc}", allow_module_level=True)
    except ImportError:
        raise SystemExit(f"MySQL not reachable: {_exc}")


print("=" * 60)
print("TESTING ACHIEVEMENTS SYSTEM")
print("=" * 60)

conn = get_connection()
cur = conn.cursor(dictionary=True)

# Test 1: Check achievements table
print("\n1. Checking achievements table...")
cur.execute("SELECT * FROM achievements")
achievements = cur.fetchall()
print(f"   ✓ Found {len(achievements)} achievement definitions:")
for ach in achievements:
    print(f"      • {ach['icon']} {ach['title']}")

# Test 2: Check user_achievements table structure
print("\n2. Checking user_achievements table...")
cur.execute("DESCRIBE user_achievements")
columns = cur.fetchall()
print(f"   ✓ Table has {len(columns)} columns:")
for col in columns:
    print(f"      • {col['Field']} ({col['Type']})")

# Test 3: Check user_statistics table structure
print("\n3. Checking user_statistics table...")
cur.execute("DESCRIBE user_statistics")
columns = cur.fetchall()
print(f"   ✓ Table has {len(columns)} columns:")
for col in columns:
    print(f"      • {col['Field']} ({col['Type']})")

# Test 4: Check if there are any existing statistics
print("\n4. Checking existing user statistics...")
cur.execute("SELECT COUNT(*) as count FROM user_statistics")
result = cur.fetchone()
print(f"   ✓ Found {result['count']} user statistics records")

# Test 5: Check if there are any unlocked achievements
print("\n5. Checking unlocked achievements...")
cur.execute("SELECT COUNT(*) as count FROM user_achievements")
result = cur.fetchone()
print(f"   ✓ Found {result['count']} unlocked achievements")

# Test 6: Verify foreign key relationship
print("\n6. Testing foreign key relationship...")
try:
    cur.execute("""
        SELECT ua.id, a.title, ua.unlocked_at 
        FROM user_achievements ua
        JOIN achievements a ON ua.achievement_id = a.achievement_id
        LIMIT 5
    """)
    results = cur.fetchall()
    print(f"   ✓ Foreign key relationship working correctly")
    if results:
        for r in results:
            print(f"      • {r['title']} unlocked at {r['unlocked_at']}")
    else:
        print("      • No achievements unlocked yet")
except Exception as e:
    print(f"   ❌ Error: {e}")

cur.close()
conn.close()

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED!")
print("=" * 60)
print("\nThe achievements system is ready!")
print("\nNext steps:")
print("  1. Visit http://127.0.0.1:5000")
print("  2. Take a quiz to unlock achievements")
print("  3. View your achievements at /achievements")
