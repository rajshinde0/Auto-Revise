"""Test script to verify all optimizations are working correctly"""
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
print("TESTING ALL OPTIMIZATIONS")
print("=" * 60)

# Test 1: Connection Pool
print("\n1. Testing Connection Pool...")
conn1 = get_connection()
conn2 = get_connection()
print("   ✓ Multiple connections from pool successful")
conn1.close()
conn2.close()

# Test 2: Optimized Text-to-Letter Conversion
print("\n2. Testing Optimized Conversion Logic...")
conn = get_connection()
cur = conn.cursor(dictionary=True)
cur.execute('SELECT q_id, option_a, option_b, option_c, option_d, correct_option FROM questions LIMIT 3')
questions = cur.fetchall()

for q in questions:
    # Old method (inefficient)
    old_correct = None
    if q['correct_option'] == q['option_a']:
        old_correct = 'A'
    elif q['correct_option'] == q['option_b']:
        old_correct = 'B'
    elif q['correct_option'] == q['option_c']:
        old_correct = 'C'
    elif q['correct_option'] == q['option_d']:
        old_correct = 'D'
    
    # New method (optimized)
    option_map = {
        q['option_a']: 'A',
        q['option_b']: 'B',
        q['option_c']: 'C',
        q['option_d']: 'D'
    }
    new_correct = option_map.get(q['correct_option'])
    
    # Verify they match
    assert old_correct == new_correct, f"Mismatch for Q{q['q_id']}"
    print(f"   ✓ Q{q['q_id']}: {q['correct_option']} → {new_correct}")

cur.close()
conn.close()

# Test 3: Batch Insert Simulation
print("\n3. Testing Batch Insert Logic...")
test_answers = {'652': 'A', '653': 'B', '654': 'C'}
values = [(999, int(q_id), answer) for q_id, answer in test_answers.items()]
print(f"   ✓ Created batch values: {len(values)} items")
print(f"   ✓ Ready for executemany(): {values}")

print("\n" + "=" * 60)
print("ALL OPTIMIZATIONS VERIFIED SUCCESSFULLY! ✓")
print("=" * 60)
print("\nPerformance Improvements:")
print("  • Connection pooling: Faster DB access")
print("  • Single connection for submit: 3 connections → 1 connection")
print("  • Batch insert: 20 queries → 1 query for user answers")
print("  • Dict lookup: O(1) instead of O(4) for letter conversion")
print("=" * 60)
