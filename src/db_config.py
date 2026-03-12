import mysql.connector
from mysql.connector import pooling
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create connection pool for better performance
connection_pool = pooling.MySQLConnectionPool(
    pool_name="mcq_pool",
    pool_size=int(os.getenv('DB_POOL_SIZE', 5)),
    pool_reset_session=True,
    host=os.getenv('DB_HOST', 'localhost'),
    user=os.getenv('DB_USER', 'root'),
    password=os.getenv('DB_PASSWORD', ''),
    database=os.getenv('DB_NAME', 'mcq_flashcards')
)

def get_connection():
    """Get connection from pool for better performance"""
    return connection_pool.get_connection()

if __name__ == "__main__":
    conn = get_connection()
    print(conn.is_connected())
    conn.close()

