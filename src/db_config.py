import mysql.connector
from mysql.connector import pooling
import logging
import os
from dotenv import load_dotenv
from contextlib import contextmanager

logger = logging.getLogger(__name__)

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
    """
    Get a connection from the pool.

    Callers must close() it (which returns it to the pool) on every code path -
    prefer the get_db_connection()/get_db_cursor() context managers below,
    which do that for you. A leaked connection is gone for the life of the
    process, and the pool is finite.
    """
    try:
        return connection_pool.get_connection()
    except Exception:
        logger.error('Error getting connection from pool', exc_info=True)
        raise

@contextmanager
def get_db_connection():
    """
    Context manager for database connections.
    Ensures the connection is always returned to the pool, including on error.

    Use this for anything that WRITES, or that needs to hand the live
    connection to a helper function. The pool runs with autocommit=False, so
    the caller is responsible for calling conn.commit() - anything uncommitted
    when the block exits is rolled back as the connection resets.

    Usage:
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(...)
            conn.commit()
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
    Context manager for a cursor with automatic connection cleanup.

    READ-ONLY. This yields only the cursor, so there is no way to commit, and
    the pool runs with autocommit=False - any INSERT/UPDATE/DELETE issued here
    is silently rolled back when the connection returns to the pool. Use
    get_db_connection() for writes.

    Usage:
        with get_db_cursor(dictionary=True) as cursor:
            cursor.execute("SELECT ...")
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
