"""
Extract complete database schema with data
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import os

# Make src/ importable so this runs from the repo root, the way the
# README documents it (python scripts/extract_schema.py).
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

from db_config import get_connection
import json

def extract_complete_schema():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    
    output = []
    
    # Header
    output.append("-- " + "="*60)
    output.append("-- MCQ QUIZ APPLICATION - COMPLETE DATABASE DUMP")
    output.append("-- Database: mcq_flashcards")
    output.append("-- Generated: 2025")
    output.append("-- " + "="*60)
    output.append("")
    
    # Get base tables only. Plain SHOW TABLES also lists views, and
    # SHOW CREATE TABLE on a view returns a 'Create View' column instead of
    # 'Create Table', which used to kill this script with a KeyError.
    cur.execute("SHOW FULL TABLES WHERE Table_type = 'BASE TABLE'")
    tables = [list(row.values())[0] for row in cur.fetchall()]

    output.append(f"-- Total Tables: {len(tables)}")
    output.append(f"-- Tables: {', '.join(tables)}")
    output.append("")
    
    output.append("CREATE DATABASE IF NOT EXISTS mcq_flashcards;")
    output.append("USE mcq_flashcards;")
    output.append("")
    
    # For each table, get CREATE TABLE and data
    for table in tables:
        output.append("")
        output.append("-- " + "="*60)
        output.append(f"-- TABLE: {table}")
        output.append("-- " + "="*60)
        output.append("")
        
        # Get CREATE TABLE statement
        cur.execute(f"SHOW CREATE TABLE `{table}`")
        create_table = cur.fetchone()['Create Table']
        output.append(create_table + ";")
        output.append("")
        
        # Get row count
        cur.execute(f"SELECT COUNT(*) as count FROM `{table}`")
        row_count = cur.fetchone()['count']
        output.append(f"-- Rows in {table}: {row_count}")
        output.append("")
        
        # Get sample data (first 5 rows for large tables, all for small)
        limit = 5 if row_count > 10 else row_count
        if row_count > 0:
            cur.execute(f"SELECT * FROM `{table}` LIMIT {limit}")
            rows = cur.fetchall()
            
            if rows:
                # Get column names
                cur.execute(f"DESCRIBE `{table}`")
                columns = [col['Field'] for col in cur.fetchall()]
                
                output.append(f"-- Sample data from {table}:")
                for row in rows:
                    values = []
                    for col in columns:
                        val = row[col]
                        if val is None:
                            values.append("NULL")
                        elif isinstance(val, str):
                            # Escape single quotes
                            escaped = val.replace("'", "''").replace("\\", "\\\\")
                            values.append(f"'{escaped}'")
                        elif isinstance(val, (int, float)):
                            values.append(str(val))
                        else:
                            values.append(f"'{str(val)}'")
                    
                    cols_str = ", ".join([f"`{col}`" for col in columns])
                    vals_str = ", ".join(values)
                    output.append(f"INSERT INTO `{table}` ({cols_str}) VALUES ({vals_str});")
                
                if row_count > limit:
                    output.append(f"-- ... and {row_count - limit} more rows")
            output.append("")
    
    # Get all queries from application
    output.append("")
    output.append("-- " + "="*60)
    output.append("-- COMMON QUERIES USED IN APPLICATION")
    output.append("-- " + "="*60)
    output.append("")
    
    queries = [
        ("User Login", "SELECT * FROM users WHERE username = ? AND is_admin = ?;"),
        ("Register User", "INSERT INTO users (username, email, password_hash, full_name, is_admin, created_at) VALUES (?, ?, ?, ?, 0, NOW());"),
        ("Rate Limiting", "SELECT COUNT(*) as attempts FROM login_attempts WHERE username = ? AND success = 0 AND attempted_at > DATE_SUB(NOW(), INTERVAL 15 MINUTE);"),
        ("Get Random Questions", "SELECT * FROM questions WHERE subject = ? ORDER BY q_id; -- Then shuffle in Python"),
        ("Save Quiz Result", "INSERT INTO results (user_id, subject, score, total_questions, percentage, time_taken, attempted_at) VALUES (?, ?, ?, ?, ?, ?, NOW());"),
        ("Get User Results", "SELECT * FROM results WHERE user_id = ? ORDER BY attempted_at DESC;"),
        ("Achievement Check", "SELECT a.* FROM achievements a WHERE a.achievement_code = ? AND NOT EXISTS (SELECT 1 FROM user_achievements ua WHERE ua.user_id = ? AND ua.achievement_id = a.achievement_id);"),
        ("Unlock Achievement", "INSERT INTO user_achievements (user_id, achievement_id, progress_when_unlocked, unlocked_at) VALUES (?, ?, ?, NOW());"),
        ("Leaderboard", "SELECT u.user_id, u.username, COUNT(r.result_id) as quizzes, ROUND(AVG(r.percentage), 2) as avg_score FROM users u LEFT JOIN results r ON u.user_id = r.user_id WHERE u.is_admin = 0 GROUP BY u.user_id ORDER BY avg_score DESC LIMIT 100;"),
        ("Update Statistics", "UPDATE user_statistics SET total_quizzes_completed = total_quizzes_completed + 1, total_questions_solved = total_questions_solved + ? WHERE user_id = ?;"),
    ]
    
    for name, query in queries:
        output.append(f"-- {name}")
        output.append(query)
        output.append("")
    
    conn.close()
    return "\n".join(output)

if __name__ == "__main__":
    schema = extract_complete_schema()

    # Write beside the other database files rather than to a bare relative
    # path, which dropped a stray copy wherever the script happened to be run
    # from.
    #
    # Deliberately NOT database/COMPLETE_DATABASE_SCHEMA.sql: that file is
    # maintained by hand and carries the foreign-key load-order guards and
    # setup notes a raw dump does not reproduce. Diff this export against it
    # rather than overwriting it.
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_path = os.path.join(repo_root, 'database', 'schema_export.sql')

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(schema)

    print(f"✅ Database schema exported to {out_path}")
    print(f"📊 File size: {len(schema)} characters")
    print("ℹ️  This is a raw dump. database/COMPLETE_DATABASE_SCHEMA.sql is the")
    print("   curated version (load-order guards, setup notes) - diff, don't clobber.")
