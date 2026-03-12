"""
Extract complete database schema with data
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

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
    
    # Get all tables
    cur.execute("SHOW TABLES")
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
    
    # Write to file
    with open("COMPLETE_DATABASE_SCHEMA.sql", "w", encoding="utf-8") as f:
        f.write(schema)
    
    print("✅ Complete database schema exported to COMPLETE_DATABASE_SCHEMA.sql")
    print(f"📊 File size: {len(schema)} characters")
