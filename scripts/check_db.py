"""Check database status after optimizations"""
from db_config import get_connection

print("=" * 60)
print("DATABASE STATUS CHECK")
print("=" * 60)

conn = get_connection()
cur = conn.cursor(dictionary=True)

# Check user_answers table
print("\n1. USER_ANSWERS TABLE:")
cur.execute("SELECT COUNT(*) as cnt FROM user_answers")
count = cur.fetchone()['cnt']
print(f"   Total records: {count}")

if count > 0:
    cur.execute("SELECT * FROM user_answers ORDER BY id DESC LIMIT 5")
    recent = cur.fetchall()
    print("\n   Recent entries:")
    for r in recent:
        print(f"     • Result #{r['result_id']}, Q{r['q_id']}: Answer={r['user_answer']}")
else:
    print("   ⚠️  No data yet - take a quiz to populate!")

# Check results table
print("\n2. RESULTS TABLE:")
cur.execute("SELECT COUNT(*) as cnt FROM results")
count = cur.fetchone()['cnt']
print(f"   Total quiz attempts: {count}")

if count > 0:
    cur.execute("SELECT * FROM results ORDER BY result_id DESC LIMIT 3")
    recent = cur.fetchall()
    print("\n   Recent quiz results:")
    for r in recent:
        print(f"     • Result #{r['result_id']}: {r['subject']} - Score: {r['score']}/{r['total_questions']} ({r['percentage']}%)")

# Check questions table
print("\n3. QUESTIONS TABLE:")
cur.execute("SELECT COUNT(*) as cnt FROM questions")
count = cur.fetchone()['cnt']
print(f"   Total questions: {count}")

cur.execute("SELECT subject, COUNT(*) as cnt FROM questions GROUP BY subject")
subjects = cur.fetchall()
print("\n   Questions by subject:")
for s in subjects:
    print(f"     • {s['subject']}: {s['cnt']} questions")

# Verify data integrity
print("\n4. DATA INTEGRITY CHECK:")
cur.execute("""
    SELECT COUNT(*) as orphaned 
    FROM user_answers ua 
    LEFT JOIN results r ON ua.result_id = r.result_id 
    WHERE r.result_id IS NULL
""")
orphaned = cur.fetchone()['orphaned']
if orphaned == 0:
    print("   ✅ All user_answers linked to valid results")
else:
    print(f"   ⚠️  {orphaned} orphaned user_answers records")

cur.close()
conn.close()

print("\n" + "=" * 60)
print("✅ DATABASE CHECK COMPLETE")
print("=" * 60)
