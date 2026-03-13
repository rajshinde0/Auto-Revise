import mysql.connector
from mysql.connector import pooling
import os
from dotenv import load_dotenv
from contextlib import contextmanager

# Load environment variables
load_dotenv()

# Create connection pool for better performance
# Increased pool size from 5 to 32 to handle concurrent requests
connection_pool = pooling.MySQLConnectionPool(
    pool_name="mcq_pool",
    pool_size=int(os.getenv('DB_POOL_SIZE', 32)),
    pool_reset_session=True,
    host=os.getenv('DB_HOST', 'localhost'),
    user=os.getenv('DB_USER', 'root'),
    password=os.getenv('DB_PASSWORD', ''),
    database=os.getenv('DB_NAME', 'mcq_flashcards'),
    autocommit=False,
    connect_timeout=10
)

def get_connection():
    """Get connection from pool for better performance"""
    try:
        return connection_pool.get_connection()
    except Exception as e:
        print(f"Error getting connection from pool: {e}")
        raise

@contextmanager
def get_db_connection():
    """
    Context manager for database connections.
    Ensures connections are always properly closed.
    
    Usage:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(...)
    """
    conn = None
    try:
        conn = get_connection()
        yield conn
    finally:
        if conn:
            conn.close()

@contextmanager
def get_db_cursor(dictionary=False):
    """
    Context manager for database cursor with automatic connection cleanup.
    
    Usage:
        with get_db_cursor(dictionary=True) as cursor:
            cursor.execute(...)
            results = cursor.fetchall()
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=dictionary)
        yield cursor
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    conn = get_connection()
    print(conn.is_connected())
    conn.close()

