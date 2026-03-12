"""
AutoRevise Flask Backend
"""

from flask import Flask, request, jsonify, session
from flask_cors import CORS
from functools import wraps
import mysql.connector
from mysql.connector import Error
import bcrypt
import os
import csv
import io
from datetime import datetime, timedelta, date
from contextlib import contextmanager
import logging
from dotenv import load_dotenv
load_dotenv()




app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

# Configure session for cross-origin cookies (local development)
# Using Lax for local development - frontend and backend must be on same domain (127.0.0.1)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Lax allows cookies on same-site requests
app.config['SESSION_COOKIE_SECURE'] = False  # False for local dev without HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = False  # Allow JavaScript access for debugging
app.config['SESSION_COOKIE_PATH'] = '/'  # Available on all paths
app.config['SESSION_COOKIE_NAME'] = 'session'  # Use default name
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  

# Configure CORS to allow credentials from multiple origins
CORS(app,
    supports_credentials=True,
    origins=[
        "http://localhost:3000", "http://127.0.0.1:3000",
        "http://127.0.0.1:5000", "http://localhost:5000",
        "http://127.0.0.1:5001", "http://localhost:5001",
        "http://127.0.0.1:5500", "http://localhost:5500",
        "http://127.0.0.1:5501", "http://localhost:5501",
        "http://127.0.0.1:5502", "http://localhost:5502",
        "http://127.0.0.1:5503", "http://localhost:5503",
        "http://127.0.0.1:8080", "http://localhost:8080",
        "null"  # allow file:// origins (sent as "null")
    ],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Content-Type"],
    max_age=3600)  # Cache preflight requests for 1 hour

@app.after_request
def after_request(response):
    """Add CORS headers to every response"""
    origin = request.headers.get('Origin')
    
    # List of allowed origins
    allowed_origins = [
        "http://localhost:3000", "http://127.0.0.1:3000",
        "http://127.0.0.1:5000", "http://localhost:5000",
        "http://127.0.0.1:5001", "http://localhost:5001",
        "http://127.0.0.1:5500", "http://localhost:5500",
        "http://127.0.0.1:5501", "http://localhost:5501",
        "http://127.0.0.1:5502", "http://localhost:5502",
        "http://127.0.0.1:5503", "http://localhost:5503",
        "http://127.0.0.1:8080", "http://localhost:8080",
        "null"
    ]
    
    if origin in allowed_origins:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    
    return response

# Database configuration
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', 'Root123'),
    'database': os.environ.get('DB_NAME', 'autorevise_db')
}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# DATABASE CONNECTION
# ============================================================================

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        yield connection
    except Error as e:
        logger.error(f"Database connection error: {e}")
        raise
    finally:
        if connection and connection.is_connected():
            connection.close()

def get_db_cursor(connection):
    """Get a dictionary cursor from connection"""
    return connection.cursor(dictionary=True)

# ============================================================================
# AUTHENTICATION DECORATOR
# ============================================================================

def login_required(f):
    """Decorator to protect routes that require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        logger.info(f"=== Authentication Check for {request.path} ===")
        logger.info(f"Request method: {request.method}")
        logger.info(f"Origin: {request.headers.get('Origin')}")
        logger.info(f"Referer: {request.headers.get('Referer')}")
        logger.info(f"Cookie header: {request.headers.get('Cookie')}")
        logger.info(f"Session keys: {list(session.keys())}")
        logger.info(f"Session data: {dict(session)}")
        logger.info(f"Has user_id in session: {'user_id' in session}")
        
        if 'user_id' not in session:
            logger.warning(f"❌ Unauthorized access to {request.path} - No user_id in session")
            return jsonify({'error': 'Authentication required'}), 401
        
        logger.info(f"✅ Authentication successful for user_id: {session.get('user_id')}")
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to protect routes that require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            logger.warning(f"Unauthorized access attempt to admin route {request.path}")
            return jsonify({'error': 'Authentication required'}), 401
        
        # Check if user is admin
        try:
            with get_db_connection() as conn:
                cursor = get_db_cursor(conn)
                cursor.execute("SELECT is_admin FROM Users WHERE user_id = %s", (session['user_id'],))
                user = cursor.fetchone()
                
                if not user or not user.get('is_admin'):
                    logger.warning(f"Non-admin user {session['user_id']} attempted to access {request.path}")
                    return jsonify({'error': 'Admin privileges required'}), 403
                
                logger.info(f"Admin access granted for user {session['user_id']} to {request.path}")
                return f(*args, **kwargs)
        except Error as e:
            logger.error(f"Admin check error: {e}")
            return jsonify({'error': 'Failed to verify admin status'}), 500
    
    return decorated_function

# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@app.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        # Validation
        if not username or not email or not password:
            return jsonify({'error': 'All fields are required'}), 400

        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400

        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        with get_db_connection() as conn:
            cursor = get_db_cursor(conn)
            
            # Check if user already exists
            cursor.execute("SELECT user_id FROM Users WHERE username = %s OR email = %s", 
                         (username, email))
            if cursor.fetchone():
                return jsonify({'error': 'Username or email already exists'}), 409

            # Insert new user
            cursor.execute(
                "INSERT INTO Users (username, email, password_hash) VALUES (%s, %s, %s)",
                (username, email, password_hash)
            )
            conn.commit()
            user_id = cursor.lastrowid

            session.permanent = True
            session['user_id'] = user_id
            session['username'] = username

            logger.info(f"New user registered: {username} (ID: {user_id})")
            return jsonify({
                'message': 'Registration successful',
                'user': {
                    'user_id': user_id,
                    'username': username,
                    'email': email,
                    'points': 0  # New users start with 0 points
                }
            }), 201

    except Error as e:
        logger.error(f"Registration error: {e}")
        return jsonify({'error': 'Registration failed'}), 500

@app.route('/login', methods=['POST'])
def login():
    """Login user and create session"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        with get_db_connection() as conn:
            cursor = get_db_cursor(conn)
            cursor.execute(
                "SELECT user_id, username, email, password_hash, points, is_admin FROM Users WHERE email = %s",
                (email,)
            )
            user = cursor.fetchone()

            if not user:
                return jsonify({'error': 'Invalid credentials'}), 401

            # Verify password
            if not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                return jsonify({'error': 'Invalid credentials'}), 401

            # Create session and make it permanent
            session.permanent = True
            session['user_id'] = user['user_id']
            session['username'] = user['username']

            logger.info(f"User logged in: {user['username']} (ID: {user['user_id']})")
            logger.info(f"Session created with ID: {session.get('user_id')}, Cookie will be set")
            logger.info(f"Session SID: {session.sid if hasattr(session, 'sid') else 'No SID'}")
            logger.info(f"Session data: {dict(session)}")
            
            response = jsonify({
                'message': 'Login successful',
                'user': {
                    'user_id': user['user_id'],
                    'username': user['username'],
                    'email': user['email'],
                    'points': user['points'],
                    'is_admin': user.get('is_admin', False)
                }
            })
            
            # Log response headers to see if Set-Cookie is present
            logger.info(f"Response headers will include: {response.headers.get('Set-Cookie', 'NO SET-COOKIE HEADER')}")
            
            return response, 200

    except Error as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': 'Login failed'}), 500

@app.route('/logout', methods=['POST'])
def logout():
    """Logout user and clear session"""
    username = session.get('username', 'Unknown')
    session.clear()
    logger.info(f"User logged out: {username}")
    return jsonify({'message': 'Logout successful'}), 200

@app.route('/make-me-admin', methods=['POST'])
@login_required
def make_me_admin():
    """Make the current logged-in user an admin (development/testing only)"""
    try:
        with get_db_connection() as conn:
            cursor = get_db_cursor(conn)
            
            # Check if user is already admin
            cursor.execute("SELECT is_admin FROM Users WHERE user_id = %s", (session['user_id'],))
            user = cursor.fetchone()
            
            if user and user['is_admin']:
                return jsonify({'message': 'You are already an admin!'}), 200
            
            # Make user admin
            cursor.execute("UPDATE Users SET is_admin = TRUE WHERE user_id = %s", (session['user_id'],))
            conn.commit()
            
            logger.info(f"User {session['user_id']} granted admin privileges")
            
            return jsonify({
                'message': 'Admin privileges granted! Please logout and login again.',
                'user_id': session['user_id']
            }), 200
            
    except Error as e:
        logger.error(f"Make admin error: {e}")
        return jsonify({'error': 'Failed to grant admin privileges'}), 500

@app.route('/session-check', methods=['GET'])
def session_check():
    """Debug endpoint to check session status"""
    return jsonify({
        'has_session': 'user_id' in session,
        'user_id': session.get('user_id'),
        'username': session.get('username'),
        'session_keys': list(session.keys()),
        'origin': request.headers.get('Origin'),
        'cookie_header': request.headers.get('Cookie'),
        'referer': request.headers.get('Referer')
    }), 200

@app.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """Get current logged-in user info"""
    try:
        with get_db_connection() as conn:
            cursor = get_db_cursor(conn)
            cursor.execute(
                "SELECT user_id, username, email, points, created_at, is_admin FROM Users WHERE user_id = %s",
                (session['user_id'],)
            )
            user = cursor.fetchone()
            
            if user:
                return jsonify({'user': user}), 200
            return jsonify({'error': 'User not found'}), 404

    except Error as e:
        logger.error(f"Get user error: {e}")
        return jsonify({'error': 'Failed to fetch user data'}), 500

# Alias for session persistence route as requested by frontend
@app.route('/auth/me', methods=['GET'])
@login_required
def get_current_user_alias():
    return get_current_user()

# ============================================================================
# DECK ROUTES
# ============================================================================

@app.route('/decks', methods=['GET'])
@login_required
def get_decks():
    """Get all decks for the logged-in user"""
    try:
        with get_db_connection() as conn:
            cursor = get_db_cursor(conn)
            cursor.execute("""
                SELECT 
                    d.deck_id,
                    d.deck_name,
                    d.description,
                    d.created_at,
                    COUNT(c.card_id) as card_count,
                    SUM(CASE WHEN cp.next_review_date <= CURDATE() THEN 1 ELSE 0 END) as cards_due
                FROM Decks d
                LEFT JOIN Cards c ON d.deck_id = c.deck_id
                LEFT JOIN CardPerformance cp ON c.card_id = cp.card_id AND cp.user_id = %s
                WHERE d.user_id = %s
                GROUP BY d.deck_id
                ORDER BY d.created_at DESC
            """, (session['user_id'], session['user_id']))
            
            decks = cursor.fetchall()
            return jsonify({'decks': decks}), 200

    except Error as e:
        logger.error(f"Get decks error: {e}")
        return jsonify({'error': 'Failed to fetch decks'}), 500

@app.route('/decks', methods=['POST'])
@login_required
def create_deck():
    """Create a new deck"""
    try:
        data = request.get_json()
        deck_name = data.get('deck_name')
        description = data.get('description', '')

        if not deck_name:
            return jsonify({'error': 'Deck name is required'}), 400

        with get_db_connection() as conn:
            cursor = get_db_cursor(conn)
            cursor.execute(
                "INSERT INTO Decks (user_id, deck_name, description) VALUES (%s, %s, %s)",
                (session['user_id'], deck_name, description)
            )
            conn.commit()
            deck_id = cursor.lastrowid

            logger.info(f"Deck created: {deck_name} (ID: {deck_id}) by user {session['user_id']}")
            
            # Check for achievement
            check_deck_achievements(conn, cursor, session['user_id'])
            
            return jsonify({
                'message': 'Deck created successfully',
                'deck_id': deck_id,
                'deck_name': deck_name,
                'description': description
            }), 201

    except Error as e:
        logger.error(f"Create deck error: {e}")
        return jsonify({'error': 'Failed to create deck'}), 500

@app.route('/decks/<int:deck_id>', methods=['GET'])
@login_required
def get_deck(deck_id):
    """Get a specific deck"""
    try:
        with get_db_connection() as conn:
            cursor = get_db_cursor(conn)
            cursor.execute("""
                SELECT d.*, COUNT(c.card_id) as card_count
                FROM Decks d
                LEFT JOIN Cards c ON d.deck_id = c.deck_id
                WHERE d.deck_id = %s AND d.user_id = %s
                GROUP BY d.deck_id
            """, (deck_id, session['user_id']))
            
            deck = cursor.fetchone()
            if not deck:
                return jsonify({'error': 'Deck not found'}), 404
            
            return jsonify({'deck': deck}), 200

    except Error as e:
        logger.error(f"Get deck error: {e}")
        return jsonify({'error': 'Failed to fetch deck'}), 500

@app.route('/decks/<int:deck_id>', methods=['DELETE'])
@login_required
def delete_deck(deck_id):
    """Delete a deck"""
    try:
        with get_db_connection() as conn:
            cursor = get_db_cursor(conn)
            
            # Check ownership
            cursor.execute("SELECT user_id FROM Decks WHERE deck_id = %s", (deck_id,))
            deck = cursor.fetchone()
            
            if not deck:
                return jsonify({'error': 'Deck not found'}), 404
            
            if deck['user_id'] != session['user_id']:
                return jsonify({'error': 'Unauthorized'}), 403
            
            cursor.execute("DELETE FROM Decks WHERE deck_id = %s", (deck_id,))
            conn.commit()
            
            logger.info(f"Deck deleted: ID {deck_id} by user {session['user_id']}")
            return jsonify({'message': 'Deck deleted successfully'}), 200

    except Error as e:
        logger.error(f"Delete deck error: {e}")
        return jsonify({'error': 'Failed to delete deck'}), 500

# ============================================================================
# CARD ROUTES
# ============================================================================

@app.route('/decks/<int:deck_id>/cards', methods=['GET'])
@login_required
def get_cards(deck_id):
    """Get all cards in a deck"""
    try:
        with get_db_connection() as conn:
            cursor = get_db_cursor(conn)
            
            # Verify deck ownership
            cursor.execute("SELECT user_id FROM Decks WHERE deck_id = %s", (deck_id,))
            deck = cursor.fetchone()
            
            if not deck:
                return jsonify({'error': 'Deck not found'}), 404
            
            if deck['user_id'] != session['user_id']:
                return jsonify({'error': 'Unauthorized'}), 403
            
            # Get cards with performance data
            cursor.execute("""
                SELECT 
                    c.card_id,
                    c.front_content,
                    c.back_content,
                    c.created_at,
                    cp.next_review_date,
                    cp.interval,
                    cp.ease_factor,
                    CASE 
                        WHEN cp.next_review_date IS NULL THEN 'new'
                        WHEN cp.next_review_date <= CURDATE() THEN 'due'
                        WHEN cp.interval < 7 THEN 'learning'
                        ELSE 'mastered'
                    END as status
                FROM Cards c
                LEFT JOIN CardPerformance cp ON c.card_id = cp.card_id AND cp.user_id = %s
                WHERE c.deck_id = %s
                ORDER BY c.created_at DESC
            """, (session['user_id'], deck_id))
            
            cards = cursor.fetchall()
            return jsonify({'cards': cards}), 200

    except Error as e:
        logger.error(f"Get cards error: {e}")
        return jsonify({'error': 'Failed to fetch cards'}), 500

@app.route('/decks/<int:deck_id>/cards', methods=['POST'])
@login_required
def create_card(deck_id):
    """Create a new card in a deck"""
    try:
        data = request.get_json()
        front_content = data.get('front_content')
        back_content = data.get('back_content')

        if not front_content or not back_content:
            return jsonify({'error': 'Both front and back content are required'}), 400

        with get_db_connection() as conn:
            cursor = get_db_cursor(conn)
            
            # Verify deck ownership
            cursor.execute("SELECT user_id FROM Decks WHERE deck_id = %s", (deck_id,))
            deck = cursor.fetchone()
            
            if not deck:
                return jsonify({'error': 'Deck not found'}), 404
            
            if deck['user_id'] != session['user_id']:
                return jsonify({'error': 'Unauthorized'}), 403
            
            # Insert card
            cursor.execute(
                "INSERT INTO Cards (deck_id, front_content, back_content) VALUES (%s, %s, %s)",
                (deck_id, front_content, back_content)
            )
            conn.commit()
            card_id = cursor.lastrowid
            
            logger.info(f"Card created: ID {card_id} in deck {deck_id}")
            
            # Check for card-related achievements
            check_card_achievements(conn, cursor, session['user_id'])
            
            return jsonify({
                'message': 'Card created successfully',
                'card_id': card_id,
                'front_content': front_content,
                'back_content': back_content
            }), 201

    except Error as e:
        logger.error(f"Create card error: {e}")
        return jsonify({'error': 'Failed to create card'}), 500

@app.route('/cards/<int:card_id>', methods=['PUT'])
@login_required
def update_card(card_id):
    """Update a card"""
    try:
        data = request.get_json()
        front_content = data.get('front_content')
        back_content = data.get('back_content')

        if not front_content or not back_content:
            return jsonify({'error': 'Both front and back content are required'}), 400

        with get_db_connection() as conn:
            cursor = get_db_cursor(conn)
            
            # Verify ownership through deck
            cursor.execute("""
                SELECT d.user_id 
                FROM Cards c 
                JOIN Decks d ON c.deck_id = d.deck_id 
                WHERE c.card_id = %s
            """, (card_id,))
            
            card = cursor.fetchone()
            if not card:
                return jsonify({'error': 'Card not found'}), 404
            
            if card['user_id'] != session['user_id']:
                return jsonify({'error': 'Unauthorized'}), 403
            
            cursor.execute(
                "UPDATE Cards SET front_content = %s, back_content = %s WHERE card_id = %s",
                (front_content, back_content, card_id)
            )
            conn.commit()
            
            return jsonify({'message': 'Card updated successfully'}), 200

    except Error as e:
        logger.error(f"Update card error: {e}")
        return jsonify({'error': 'Failed to update card'}), 500

@app.route('/cards/<int:card_id>', methods=['DELETE'])
@login_required
def delete_card(card_id):
    """Delete a card"""
    try:
        with get_db_connection() as conn:
            cursor = get_db_cursor(conn)
            
            # Verify ownership through deck
            cursor.execute("""
                SELECT d.user_id 
                FROM Cards c 
                JOIN Decks d ON c.deck_id = d.deck_id 
                WHERE c.card_id = %s
            """, (card_id,))
            
            card = cursor.fetchone()
            if not card:
                return jsonify({'error': 'Card not found'}), 404
            
            if card['user_id'] != session['user_id']:
                return jsonify({'error': 'Unauthorized'}), 403
            
            cursor.execute("DELETE FROM Cards WHERE card_id = %s", (card_id,))
            conn.commit()
            
            return jsonify({'message': 'Card deleted successfully'}), 200

    except Error as e:
        logger.error(f"Delete card error: {e}")
        return jsonify({'error': 'Failed to delete card'}), 500

@app.route('/decks/<int:deck_id>/upload-cards', methods=['POST'])
@login_required
def upload_cards_bulk(deck_id):
    """Bulk upload cards from CSV data"""
    try:
        data = request.get_json()
        cards_data = data.get('cards', [])

        if not cards_data or not isinstance(cards_data, list):
            return jsonify({'error': 'Invalid cards data. Expected array of cards.'}), 400

        with get_db_connection() as conn:
            cursor = get_db_cursor(conn)
            
            # Verify deck ownership
            cursor.execute("SELECT user_id FROM Decks WHERE deck_id = %s", (deck_id,))
            deck = cursor.fetchone()
            
            if not deck:
                return jsonify({'error': 'Deck not found'}), 404
            
            if deck['user_id'] != session['user_id']:
                return jsonify({'error': 'Unauthorized'}), 403
            
            # Validate and insert cards
            inserted_count = 0
            failed_cards = []
            
            for idx, card in enumerate(cards_data):
                front_content = card.get('front_content') or card.get('Question') or card.get('question')
                back_content = card.get('back_content') or card.get('Answer') or card.get('answer')
                
                if not front_content or not back_content:
                    failed_cards.append({
                        'index': idx + 1,
                        'reason': 'Missing question or answer'
                    })
                    continue
                
                try:
                    cursor.execute(
                        "INSERT INTO Cards (deck_id, front_content, back_content) VALUES (%s, %s, %s)",
                        (deck_id, str(front_content).strip(), str(back_content).strip())
                    )
                    inserted_count += 1
                except Error as e:
                    failed_cards.append({
                        'index': idx + 1,
                        'reason': str(e)
                    })
            
            conn.commit()
            
            # Check for achievements
            if inserted_count > 0:
                check_card_achievements(conn, cursor, session['user_id'])
            
            logger.info(f"Bulk upload: {inserted_count} cards added to deck {deck_id} by user {session['user_id']}")
            
            response = {
                'message': f'Successfully added {inserted_count} card(s)',
                'inserted': inserted_count,
                'failed': len(failed_cards),
                'total': len(cards_data)
            }
            
            if failed_cards:
                response['failed_cards'] = failed_cards
            
            return jsonify(response), 201

    except Error as e:
        logger.error(f"Bulk upload error: {e}")
        return jsonify({'error': 'Failed to upload cards'}), 500

# ============================================================================
# SPACED REPETITION STUDY SYSTEM
# ============================================================================

@app.route('/study-session', methods=['GET'])
@login_required
def get_study_session():
    """Get cards due for review"""
    try:
        deck_id = request.args.get('deck_id', type=int)
        limit = request.args.get('limit', default=20, type=int)

        with get_db_connection() as conn:
            cursor = get_db_cursor(conn)
            
            # Build query based on whether deck_id is specified
            if deck_id:
                # Verify deck ownership
                cursor.execute("SELECT user_id FROM Decks WHERE deck_id = %s", (deck_id,))
                deck = cursor.fetchone()
                
                if not deck:
                    return jsonify({'error': 'Deck not found'}), 404
                
                if deck['user_id'] != session['user_id']:
                    return jsonify({'error': 'Unauthorized'}), 403
                
                # Get due cards from specific deck
                query = """
                    SELECT 
                        c.card_id,
                        c.deck_id,
                        c.front_content,
                        c.back_content,
                        d.deck_name,
                        cp.next_review_date,
                        cp.interval,
                        cp.ease_factor
                    FROM Cards c
                    JOIN Decks d ON c.deck_id = d.deck_id
                    LEFT JOIN CardPerformance cp ON c.card_id = cp.card_id AND cp.user_id = %s
                    WHERE d.deck_id = %s AND d.user_id = %s
                    AND (cp.next_review_date IS NULL OR cp.next_review_date <= CURDATE())
                    ORDER BY cp.next_review_date ASC, c.created_at ASC
                    LIMIT %s
                """
                cursor.execute(query, (session['user_id'], deck_id, session['user_id'], limit))
            else:
                # Get due cards from all decks
                query = """
                    SELECT 
                        c.card_id,
                        c.deck_id,
                        c.front_content,
                        c.back_content,
                        d.deck_name,
                        cp.next_review_date,
                        cp.interval,
                        cp.ease_factor
                    FROM Cards c
                    JOIN Decks d ON c.deck_id = d.deck_id
                    LEFT JOIN CardPerformance cp ON c.card_id = cp.card_id AND cp.user_id = %s
                    WHERE d.user_id = %s
                    AND (cp.next_review_date IS NULL OR cp.next_review_date <= CURDATE())
                    ORDER BY cp.next_review_date ASC, c.created_at ASC
                    LIMIT %s
                """
                cursor.execute(query, (session['user_id'], session['user_id'], limit))
            
            cards = cursor.fetchall()
            return jsonify({
                'cards': cards,
                'total': len(cards)
            }), 200

    except Error as e:
        logger.error(f"Get study session error: {e}")
        return jsonify({'error': 'Failed to fetch study cards'}), 500

@app.route('/submit-review', methods=['POST'])
@login_required
def submit_review():
    """Submit a card review and update spaced repetition data"""
    try:
        data = request.get_json()
        card_id = data.get('card_id')
        rating = data.get('rating')  # 'forgot', 'hard', 'good', 'easy'

        if not card_id or not rating:
            return jsonify({'error': 'card_id and rating are required'}), 400

        if rating not in ['forgot', 'hard', 'good', 'easy']:
            return jsonify({'error': 'Invalid rating'}), 400

        with get_db_connection() as conn:
            cursor = get_db_cursor(conn)
            
            # Verify card ownership
            cursor.execute("""
                SELECT d.user_id 
                FROM Cards c 
                JOIN Decks d ON c.deck_id = d.deck_id 
                WHERE c.card_id = %s
            """, (card_id,))
            
            card = cursor.fetchone()
            if not card:
                return jsonify({'error': 'Card not found'}), 404
            
            if card['user_id'] != session['user_id']:
                return jsonify({'error': 'Unauthorized'}), 403
            
            # Get current performance data
            cursor.execute("""
                SELECT * FROM CardPerformance 
                WHERE user_id = %s AND card_id = %s
            """, (session['user_id'], card_id))
            
            performance = cursor.fetchone()
            
            # Calculate new values using SM-2 algorithm
            if performance:
                current_interval = performance['interval']
                current_ease = float(performance['ease_factor'])
            else:
                current_interval = 0
                current_ease = 2.5
            
            # Update based on rating
            new_interval, new_ease = calculate_sm2(rating, current_interval, current_ease)
            next_review = date.today() + timedelta(days=new_interval)
            
            # Update or insert performance record
            if performance:
                cursor.execute("""
                    UPDATE CardPerformance 
                    SET next_review_date = %s, `interval` = %s, ease_factor = %s
                    WHERE user_id = %s AND card_id = %s
                """, (next_review, new_interval, new_ease, session['user_id'], card_id))
            else:
                cursor.execute("""
                    INSERT INTO CardPerformance (user_id, card_id, next_review_date, `interval`, ease_factor)
                    VALUES (%s, %s, %s, %s, %s)
                """, (session['user_id'], card_id, next_review, new_interval, new_ease))
            
            # Award points based on rating
            points_map = {'forgot': 5, 'hard': 10, 'good': 15, 'easy': 20}
            points = points_map[rating]
            
            cursor.execute(
                "UPDATE Users SET points = points + %s WHERE user_id = %s",
                (points, session['user_id'])
            )
            
            # Log study activity
            today = date.today()
            cursor.execute("""
                INSERT INTO StudyLog (user_id, study_date, cards_reviewed)
                VALUES (%s, %s, 1)
                ON DUPLICATE KEY UPDATE cards_reviewed = cards_reviewed + 1
            """, (session['user_id'], today))
            
            conn.commit()
            
            # Check for achievements
            check_study_achievements(conn, cursor, session['user_id'])
            
            logger.info(f"Review submitted: Card {card_id}, Rating {rating}, User {session['user_id']}")
            
            return jsonify({
                'message': 'Review submitted successfully',
                'next_review_date': next_review.isoformat(),
                'interval': new_interval,
                'points_earned': points
            }), 200

    except Error as e:
        logger.error(f"Submit review error: {e}")
        return jsonify({'error': 'Failed to submit review'}), 500

def calculate_sm2(rating, current_interval, current_ease):
    """
    SM-2 Spaced Repetition Algorithm
    Returns: (new_interval, new_ease_factor)
    """
    # Rating to quality mapping (0-5 scale)
    quality_map = {
        'forgot': 0,  # Complete blackout
        'hard': 3,    # Correct response with serious difficulty
        'good': 4,    # Correct response with hesitation
        'easy': 5     # Perfect response
    }
    
    quality = quality_map[rating]
    
    # Calculate new ease factor
    new_ease = current_ease + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    new_ease = max(1.3, new_ease)  # Minimum ease factor is 1.3
    
    # Calculate new interval
    if quality < 3:
        # Failed - restart
        new_interval = 1
    else:
        if current_interval == 0:
            new_interval = 1
        elif current_interval == 1:
            new_interval = 6
        else:
            new_interval = round(current_interval * new_ease)
    
    return new_interval, round(new_ease, 2)

# ============================================================================
# STUDY LOG ROUTES
# ============================================================================

@app.route('/studylog', methods=['GET'])
@login_required
def get_study_log():
    """Get recent study activity for the logged-in user"""
    try:
        limit = request.args.get('limit', default=30, type=int)
        with get_db_connection() as conn:
            cursor = get_db_cursor(conn)
            cursor.execute(
                """
                SELECT study_date, cards_reviewed
                FROM StudyLog
                WHERE user_id = %s
                ORDER BY study_date DESC
                LIMIT %s
                """,
                (session['user_id'], limit)
            )
            logs = cursor.fetchall()
            return jsonify({'logs': logs}), 200
    except Error as e:
        logger.error(f"Get study log error: {e}")
        return jsonify({'error': 'Failed to fetch study log'}), 500

@app.route('/studylog', methods=['POST'])
@login_required
def add_study_log():
    """Add or update today's study activity"""
    try:
        data = request.get_json() or {}
        count = int(data.get('cards_reviewed', 1))
        today = date.today()
        with get_db_connection() as conn:
            cursor = get_db_cursor(conn)
            cursor.execute(
                """
                INSERT INTO StudyLog (user_id, study_date, cards_reviewed)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE cards_reviewed = cards_reviewed + VALUES(cards_reviewed)
                """,
                (session['user_id'], today, count)
            )
            conn.commit()
            return jsonify({'message': 'Study log updated', 'cards_reviewed_added': count}), 200
    except Error as e:
        logger.error(f"Add study log error: {e}")
        return jsonify({'error': 'Failed to update study log'}), 500

# ============================================================================
# STATISTICS
# ============================================================================

@app.route('/stats', methods=['GET'])
@login_required
def get_stats():
    """Get user statistics"""
    try:
        with get_db_connection() as conn:
            cursor = get_db_cursor(conn)
            
            # Total decks
            cursor.execute(
                "SELECT COUNT(*) as total FROM Decks WHERE user_id = %s",
                (session['user_id'],)
            )
            total_decks = cursor.fetchone()['total']
            
            # Total cards
            cursor.execute("""
                SELECT COUNT(*) as total 
                FROM Cards c 
                JOIN Decks d ON c.deck_id = d.deck_id 
                WHERE d.user_id = %s
            """, (session['user_id'],))
            total_cards = cursor.fetchone()['total']
            
            # Cards due today
            cursor.execute("""
                SELECT COUNT(*) as total 
                FROM CardPerformance cp 
                WHERE cp.user_id = %s AND cp.next_review_date <= CURDATE()
            """, (session['user_id'],))
            cards_due = cursor.fetchone()['total']
            
            # Cards due in next 7 days
            cursor.execute("""
                SELECT COUNT(*) as total 
                FROM CardPerformance cp 
                WHERE cp.user_id = %s 
                AND cp.next_review_date > CURDATE() 
                AND cp.next_review_date <= DATE_ADD(CURDATE(), INTERVAL 7 DAY)
            """, (session['user_id'],))
            cards_upcoming = cursor.fetchone()['total']
            
            # New cards (never reviewed)
            cursor.execute("""
                SELECT COUNT(*) as total 
                FROM Cards c 
                JOIN Decks d ON c.deck_id = d.deck_id 
                LEFT JOIN CardPerformance cp ON c.card_id = cp.card_id AND cp.user_id = %s
                WHERE d.user_id = %s AND cp.card_id IS NULL
            """, (session['user_id'], session['user_id']))
            new_cards = cursor.fetchone()['total']
            
            # Current streak
            cursor.execute("""
                SELECT study_date 
                FROM StudyLog 
                WHERE user_id = %s 
                ORDER BY study_date DESC
            """, (session['user_id'],))
            
            study_dates = [row['study_date'] for row in cursor.fetchall()]
            current_streak = calculate_streak(study_dates)
            
            # Total points
            cursor.execute(
                "SELECT points FROM Users WHERE user_id = %s",
                (session['user_id'],)
            )
            total_points = cursor.fetchone()['points']
            
            # Cards reviewed today
            today = date.today()
            cursor.execute("""
                SELECT COALESCE(cards_reviewed, 0) as cards_reviewed
                FROM StudyLog 
                WHERE user_id = %s AND study_date = %s
            """, (session['user_id'], today))
            
            result = cursor.fetchone()
            cards_reviewed_today = result['cards_reviewed'] if result else 0
            
            return jsonify({
                'stats': {
                    'total_decks': total_decks,
                    'total_cards': total_cards,
                    'cards_due': cards_due,
                    'cards_upcoming': cards_upcoming,
                    'new_cards': new_cards,
                    'current_streak': current_streak,
                    'total_points': total_points,
                    'cards_reviewed_today': cards_reviewed_today
                }
            }), 200

    except Error as e:
        logger.error(f"Get stats error: {e}")
        return jsonify({'error': 'Failed to fetch statistics'}), 500

def calculate_streak(study_dates):
    """Calculate current study streak from list of study dates"""
    if not study_dates:
        return 0
    
    today = date.today()
    streak = 0
    
    # Check if studied today or yesterday to start counting
    if study_dates[0] == today or study_dates[0] == today - timedelta(days=1):
        expected_date = today if study_dates[0] == today else today - timedelta(days=1)
        
        for study_date in study_dates:
            if study_date == expected_date:
                streak += 1
                expected_date -= timedelta(days=1)
            else:
                break
    
    return streak

# ============================================================================
# GAMIFICATION - ACHIEVEMENTS
# ============================================================================

@app.route('/achievements', methods=['GET'])
@login_required
def get_achievements():
    """Get all achievements and user's earned achievements"""
    try:
        with get_db_connection() as conn:
            cursor = get_db_cursor(conn)
            
            # Get all achievements with user's earned status
            cursor.execute("""
                SELECT 
                    a.achievement_id,
                    a.name,
                    a.description,
                    a.icon_url,
                    CASE WHEN ua.user_id IS NOT NULL THEN 1 ELSE 0 END as earned,
                    ua.earned_at
                FROM Achievements a
                LEFT JOIN UserAchievements ua ON a.achievement_id = ua.achievement_id 
                    AND ua.user_id = %s
                ORDER BY earned DESC, a.achievement_id ASC
            """, (session['user_id'],))
            
            achievements = cursor.fetchall()
            
            return jsonify({
                'achievements': achievements,
                'total': len(achievements),
                'earned': sum(1 for a in achievements if a['earned'])
            }), 200

    except Error as e:
        logger.error(f"Get achievements error: {e}")
        return jsonify({'error': 'Failed to fetch achievements'}), 500

@app.route('/check-achievements', methods=['POST'])
@login_required
def check_achievements():
    """Check and award new achievements"""
    try:
        with get_db_connection() as conn:
            cursor = get_db_cursor(conn)
            
            new_achievements = []
            
            # Check all achievement types
            new_achievements.extend(check_deck_achievements(conn, cursor, session['user_id']))
            new_achievements.extend(check_card_achievements(conn, cursor, session['user_id']))
            new_achievements.extend(check_study_achievements(conn, cursor, session['user_id']))
            
            return jsonify({
                'message': 'Achievements checked',
                'new_achievements': new_achievements
            }), 200

    except Error as e:
        logger.error(f"Check achievements error: {e}")
        return jsonify({'error': 'Failed to check achievements'}), 500

def check_deck_achievements(conn, cursor, user_id):
    """Check and award deck-related achievements"""
    new_achievements = []
    
    try:
        # Count user's decks
        cursor.execute("SELECT COUNT(*) as count FROM Decks WHERE user_id = %s", (user_id,))
        deck_count = cursor.fetchone()['count']
        
        # First Steps - Create first deck
        if deck_count >= 1:
            new_achievements.extend(award_achievement(conn, cursor, user_id, 'First Steps'))
        
    except Error as e:
        logger.error(f"Check deck achievements error: {e}")
    
    return new_achievements

def check_card_achievements(conn, cursor, user_id):
    """Check and award card-related achievements"""
    new_achievements = []
    
    try:
        # Count user's total cards
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM Cards c 
            JOIN Decks d ON c.deck_id = d.deck_id 
            WHERE d.user_id = %s
        """, (user_id,))
        card_count = cursor.fetchone()['count']
        
        # Card Collector - 50 cards
        if card_count >= 50:
            new_achievements.extend(award_achievement(conn, cursor, user_id, 'Card Collector'))
        
        # Knowledge Builder - 250 cards
        if card_count >= 250:
            new_achievements.extend(award_achievement(conn, cursor, user_id, 'Knowledge Builder'))
        
    except Error as e:
        logger.error(f"Check card achievements error: {e}")
    
    return new_achievements

def check_study_achievements(conn, cursor, user_id):
    """Check and award study-related achievements"""
    new_achievements = []
    
    try:
        # Check if user has any study sessions
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM StudyLog 
            WHERE user_id = %s
        """, (user_id,))
        
        if cursor.fetchone()['count'] > 0:
            new_achievements.extend(award_achievement(conn, cursor, user_id, 'Dedicated Learner'))
        
        # Get study dates for streak calculation
        cursor.execute("""
            SELECT study_date 
            FROM StudyLog 
            WHERE user_id = %s 
            ORDER BY study_date DESC
        """, (user_id,))
        
        study_dates = [row['study_date'] for row in cursor.fetchall()]
        current_streak = calculate_streak(study_dates)
        
        # 7-Day Streak
        if current_streak >= 7:
            new_achievements.extend(award_achievement(conn, cursor, user_id, '7-Day Streak'))
        
        # 30-Day Streak
        if current_streak >= 30:
            new_achievements.extend(award_achievement(conn, cursor, user_id, '30-Day Streak'))
        
    except Error as e:
        logger.error(f"Check study achievements error: {e}")
    
    return new_achievements

def award_achievement(conn, cursor, user_id, achievement_name):
    """Award an achievement to a user if not already earned"""
    try:
        # Get achievement ID
        cursor.execute(
            "SELECT achievement_id FROM Achievements WHERE name = %s",
            (achievement_name,)
        )
        achievement = cursor.fetchone()
        
        if not achievement:
            return []
        
        achievement_id = achievement['achievement_id']
        
        # Check if already earned
        cursor.execute("""
            SELECT * FROM UserAchievements 
            WHERE user_id = %s AND achievement_id = %s
        """, (user_id, achievement_id))
        
        if cursor.fetchone():
            return []  # Already earned
        
        # Award achievement
        cursor.execute("""
            INSERT INTO UserAchievements (user_id, achievement_id) 
            VALUES (%s, %s)
        """, (user_id, achievement_id))
        
        # Bonus points for earning achievement
        cursor.execute(
            "UPDATE Users SET points = points + 100 WHERE user_id = %s",
            (user_id,)
        )
        
        conn.commit()
        
        logger.info(f"Achievement awarded: {achievement_name} to user {user_id}")
        return [{'name': achievement_name, 'achievement_id': achievement_id}]
        
    except Error as e:
        logger.error(f"Award achievement error: {e}")
        return []

# ============================================================================
# MCQ ROUTES
# ============================================================================

@app.route('/mcq/categories', methods=['GET'])
@login_required
def get_mcq_categories():
    """Get all MCQ categories"""
    try:
        with get_db_connection() as conn:
            cursor = get_db_cursor(conn)
            
            cursor.execute("""
                SELECT category_id, category_name, description, icon, created_at
                FROM MCQ_Categories
                ORDER BY category_name
            """)
            
            categories = cursor.fetchall()
            
            # Get question count per category
            for category in categories:
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM MCQ_Questions
                    WHERE category_id = %s
                """, (category['category_id'],))
                
                count_result = cursor.fetchone()
                category['question_count'] = count_result['count'] if count_result else 0
            
            return jsonify({'categories': categories}), 200
    
    except Error as e:
        logger.error(f"Get categories error: {e}")
        return jsonify({'error': 'Failed to fetch categories'}), 500


@app.route('/mcq/category/<int:category_id>', methods=['GET'])
@login_required
def get_mcqs_by_category(category_id):
    """Get all MCQs for a specific category"""
    try:
        with get_db_connection() as conn:
            cursor = get_db_cursor(conn)
            
            # Get category info
            cursor.execute("""
                SELECT category_id, category_name, description, icon
                FROM MCQ_Categories
                WHERE category_id = %s
            """, (category_id,))
            
            category = cursor.fetchone()
            
            if not category:
                return jsonify({'error': 'Category not found'}), 404
            
            # Get MCQs for this category
            query = """
                SELECT 
                    m.mcq_id, m.question_text, m.option_a, m.option_b, m.option_c, m.option_d,
                    m.difficulty, m.created_at, d.deck_name
                FROM MCQ_Questions m
                LEFT JOIN Decks d ON m.deck_id = d.deck_id
                WHERE m.category_id = %s
                ORDER BY m.created_at DESC
            """
            cursor.execute(query, (category_id,))
            mcqs = cursor.fetchall()
            
            return jsonify({
                'category': category,
                'mcqs': mcqs,
                'total': len(mcqs)
            }), 200
    
    except Error as e:
        logger.error(f"Get MCQs by category error: {e}")
        return jsonify({'error': 'Failed to fetch MCQs'}), 500


@app.route('/mcq/upload', methods=['POST'])
@admin_required
def upload_mcq_csv():
    """Admin-only: Upload MCQs from CSV file"""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'File must be a CSV'}), 400
        
        # Get category_id from form data (optional)
        category_id = request.form.get('category_id')
        if category_id:
            category_id = int(category_id)
        else:
            category_id = None
        
        # Read CSV file
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream)
        
        # Validate required columns
        required_columns = ['question_text', 'option_a', 'option_b', 'option_c', 'option_d', 
                          'correct_option', 'deck_id']
        
        if not all(col in csv_reader.fieldnames for col in required_columns):
            return jsonify({
                'error': 'CSV missing required columns',
                'required': required_columns,
                'found': csv_reader.fieldnames
            }), 400
        
        successful_imports = 0
        failed_imports = 0
        errors = []
        
        with get_db_connection() as conn:
            cursor = get_db_cursor(conn)
            
            # If category_id provided, verify it exists
            if category_id:
                cursor.execute("SELECT category_id FROM MCQ_Categories WHERE category_id = %s", (category_id,))
                if not cursor.fetchone():
                    return jsonify({'error': f'Category {category_id} does not exist'}), 400
            
            for row_num, row in enumerate(csv_reader, start=2):  # start=2 because row 1 is header
                try:
                    # Validate required fields
                    question_text = row.get('question_text', '').strip()
                    option_a = row.get('option_a', '').strip()
                    option_b = row.get('option_b', '').strip()
                    option_c = row.get('option_c', '').strip()
                    option_d = row.get('option_d', '').strip()
                    correct_option = row.get('correct_option', '').strip().upper()
                    deck_id = row.get('deck_id', '').strip()
                    
                    # Optional fields
                    explanation = row.get('explanation', '').strip() or None
                    difficulty = row.get('difficulty', 'medium').strip().lower()
                    
                    # Category can come from CSV or form data
                    row_category_id = row.get('category_id', '').strip()
                    if row_category_id and row_category_id.isdigit():
                        final_category_id = int(row_category_id)
                    else:
                        final_category_id = category_id  # Use form data category
                    
                    # Validation
                    if not question_text:
                        raise ValueError("Question text cannot be empty")
                    
                    if not all([option_a, option_b, option_c, option_d]):
                        raise ValueError("All four options must be provided")
                    
                    if correct_option not in ['A', 'B', 'C', 'D']:
                        raise ValueError(f"Correct option must be A, B, C, or D, got: {correct_option}")
                    
                    if difficulty not in ['easy', 'medium', 'hard']:
                        raise ValueError(f"Difficulty must be easy, medium, or hard, got: {difficulty}")
                    
                    if not deck_id or not deck_id.isdigit():
                        raise ValueError(f"Invalid deck_id: {deck_id}")
                    
                    deck_id = int(deck_id)
                    
                    # Check if deck exists
                    cursor.execute("SELECT deck_id FROM Decks WHERE deck_id = %s", (deck_id,))
                    if not cursor.fetchone():
                        raise ValueError(f"Deck {deck_id} does not exist")
                    
                    # Insert MCQ with category
                    insert_query = """
                        INSERT INTO MCQ_Questions 
                        (deck_id, category_id, question_text, option_a, option_b, option_c, option_d, 
                         correct_option, explanation, difficulty, created_by)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(insert_query, (
                        deck_id, final_category_id, question_text, option_a, option_b, option_c, option_d,
                        correct_option, explanation, difficulty, session['user_id']
                    ))
                    
                    successful_imports += 1
                    
                except Exception as row_error:
                    failed_imports += 1
                    errors.append({
                        'row': row_num,
                        'error': str(row_error),
                        'data': row
                    })
                    logger.error(f"Error importing row {row_num}: {row_error}")
            
            # Log the upload with category
            log_query = """
                INSERT INTO MCQ_Upload_Log 
                (admin_id, filename, category_id, total_questions, successful_imports, failed_imports)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            total_questions = successful_imports + failed_imports
            cursor.execute(log_query, (
                session['user_id'], file.filename, category_id, total_questions, 
                successful_imports, failed_imports
            ))
            
            conn.commit()
        
        return jsonify({
            'message': 'MCQ upload completed',
            'total_processed': successful_imports + failed_imports,
            'successful': successful_imports,
            'failed': failed_imports,
            'errors': errors[:10]  # Return first 10 errors
        }), 200 if failed_imports == 0 else 207  # 207 Multi-Status if there were partial failures
    
    except Error as e:
        logger.error(f"MCQ upload error: {e}")
        return jsonify({'error': 'Failed to upload MCQs', 'details': str(e)}), 500
    except Exception as e:
        logger.error(f"Unexpected MCQ upload error: {e}")
        return jsonify({'error': 'Unexpected error during upload', 'details': str(e)}), 500


@app.route('/mcq/deck/<int:deck_id>', methods=['GET'])
@login_required
def get_deck_mcqs(deck_id):
    """Get all MCQs for a specific deck (questions only, no answers for students)"""
    try:
        with get_db_connection() as conn:
            cursor = get_db_cursor(conn)
            
            # Verify deck access
            cursor.execute("SELECT user_id FROM Decks WHERE deck_id = %s", (deck_id,))
            deck = cursor.fetchone()
            
            if not deck:
                return jsonify({'error': 'Deck not found'}), 404
            
            if deck['user_id'] != session['user_id']:
                return jsonify({'error': 'Unauthorized'}), 403
            
            # Get MCQs
            query = """
                SELECT 
                    mcq_id, question_text, option_a, option_b, option_c, option_d,
                    difficulty, created_at
                FROM MCQ_Questions
                WHERE deck_id = %s
                ORDER BY created_at DESC
            """
            cursor.execute(query, (deck_id,))
            mcqs = cursor.fetchall()
            
            return jsonify({
                'mcqs': mcqs,
                'total': len(mcqs)
            }), 200
    
    except Error as e:
        logger.error(f"Get deck MCQs error: {e}")
        return jsonify({'error': 'Failed to fetch MCQs'}), 500


@app.route('/mcq/<int:mcq_id>/check', methods=['POST'])
@login_required
def check_mcq_answer(mcq_id):
    """Check if the user's answer is correct and update performance"""
    try:
        data = request.get_json()
        user_answer = data.get('answer', '').strip().upper()
        
        if user_answer not in ['A', 'B', 'C', 'D']:
            return jsonify({'error': 'Invalid answer. Must be A, B, C, or D'}), 400
        
        with get_db_connection() as conn:
            cursor = get_db_cursor(conn)
            
            # Get MCQ details
            cursor.execute("""
                SELECT mcq_id, correct_option, explanation, deck_id
                FROM MCQ_Questions
                WHERE mcq_id = %s
            """, (mcq_id,))
            
            mcq = cursor.fetchone()
            
            if not mcq:
                return jsonify({'error': 'MCQ not found'}), 404
            
            # Verify user has access to this deck
            cursor.execute("""
                SELECT user_id FROM Decks WHERE deck_id = %s
            """, (mcq['deck_id'],))
            
            deck = cursor.fetchone()
            if not deck or deck['user_id'] != session['user_id']:
                return jsonify({'error': 'Unauthorized'}), 403
            
            is_correct = (user_answer == mcq['correct_option'])
            
            # Update or insert MCQ performance
            cursor.execute("""
                SELECT mcq_performance_id, times_attempted, times_correct
                FROM MCQ_Performance
                WHERE user_id = %s AND mcq_id = %s
            """, (session['user_id'], mcq_id))
            
            performance = cursor.fetchone()
            
            if performance:
                # Update existing performance
                new_attempts = performance['times_attempted'] + 1
                new_correct = performance['times_correct'] + (1 if is_correct else 0)
                
                # Calculate next review date (simple spaced repetition)
                if is_correct:
                    interval_days = min(new_correct * 2, 30)  # Max 30 days
                else:
                    interval_days = 1  # Review tomorrow if incorrect
                
                next_review = datetime.now().date() + timedelta(days=interval_days)
                
                cursor.execute("""
                    UPDATE MCQ_Performance
                    SET times_attempted = %s, times_correct = %s, 
                        last_attempt_date = NOW(), next_review_date = %s
                    WHERE user_id = %s AND mcq_id = %s
                """, (new_attempts, new_correct, next_review, session['user_id'], mcq_id))
            else:
                # Insert new performance record
                next_review = datetime.now().date() + timedelta(days=(2 if is_correct else 1))
                
                cursor.execute("""
                    INSERT INTO MCQ_Performance 
                    (user_id, mcq_id, times_attempted, times_correct, next_review_date)
                    VALUES (%s, %s, 1, %s, %s)
                """, (session['user_id'], mcq_id, (1 if is_correct else 0), next_review))
            
            # Award points if correct
            if is_correct:
                cursor.execute("""
                    UPDATE Users SET points = points + 5 WHERE user_id = %s
                """, (session['user_id'],))
            
            conn.commit()
            
            return jsonify({
                'correct': is_correct,
                'correct_answer': mcq['correct_option'],
                'explanation': mcq['explanation'],
                'points_earned': 5 if is_correct else 0
            }), 200
    
    except Error as e:
        logger.error(f"Check MCQ answer error: {e}")
        return jsonify({'error': 'Failed to check answer'}), 500


@app.route('/mcq/study-session', methods=['GET'])
@login_required
def get_mcq_study_session():
    """Get MCQs due for review across all user's decks"""
    try:
        deck_id = request.args.get('deck_id', type=int)
        limit = request.args.get('limit', default=10, type=int)
        
        with get_db_connection() as conn:
            cursor = get_db_cursor(conn)
            
            if deck_id:
                # Verify deck ownership
                cursor.execute("SELECT user_id FROM Decks WHERE deck_id = %s", (deck_id,))
                deck = cursor.fetchone()
                
                if not deck:
                    return jsonify({'error': 'Deck not found'}), 404
                
                if deck['user_id'] != session['user_id']:
                    return jsonify({'error': 'Unauthorized'}), 403
                
                # Get MCQs from specific deck
                query = """
                    SELECT 
                        m.mcq_id, m.question_text, m.option_a, m.option_b, 
                        m.option_c, m.option_d, m.difficulty,
                        d.deck_name,
                        p.next_review_date, p.times_attempted, p.times_correct
                    FROM MCQ_Questions m
                    JOIN Decks d ON m.deck_id = d.deck_id
                    LEFT JOIN MCQ_Performance p ON m.mcq_id = p.mcq_id AND p.user_id = %s
                    WHERE m.deck_id = %s
                    AND (p.next_review_date IS NULL OR p.next_review_date <= CURDATE())
                    ORDER BY p.next_review_date ASC, m.created_at ASC
                    LIMIT %s
                """
                cursor.execute(query, (session['user_id'], deck_id, limit))
            else:
                # Get MCQs from all user's decks
                query = """
                    SELECT 
                        m.mcq_id, m.question_text, m.option_a, m.option_b, 
                        m.option_c, m.option_d, m.difficulty,
                        d.deck_name,
                        p.next_review_date, p.times_attempted, p.times_correct
                    FROM MCQ_Questions m
                    JOIN Decks d ON m.deck_id = d.deck_id
                    LEFT JOIN MCQ_Performance p ON m.mcq_id = p.mcq_id AND p.user_id = %s
                    WHERE d.user_id = %s
                    AND (p.next_review_date IS NULL OR p.next_review_date <= CURDATE())
                    ORDER BY p.next_review_date ASC, m.created_at ASC
                    LIMIT %s
                """
                cursor.execute(query, (session['user_id'], session['user_id'], limit))
            
            mcqs = cursor.fetchall()
            
            return jsonify({
                'mcqs': mcqs,
                'total': len(mcqs)
            }), 200
    
    except Error as e:
        logger.error(f"Get MCQ study session error: {e}")
        return jsonify({'error': 'Failed to fetch MCQ study session'}), 500


@app.route('/mcq/stats', methods=['GET'])
@login_required
def get_mcq_stats():
    """Get user's MCQ performance statistics"""
    try:
        with get_db_connection() as conn:
            cursor = get_db_cursor(conn)
            
            # Overall MCQ stats
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT mcq_id) as total_mcqs_attempted,
                    SUM(times_attempted) as total_attempts,
                    SUM(times_correct) as total_correct,
                    ROUND(AVG(times_correct / times_attempted * 100), 2) as avg_accuracy
                FROM MCQ_Performance
                WHERE user_id = %s AND times_attempted > 0
            """, (session['user_id'],))
            
            overall = cursor.fetchone() or {
                'total_mcqs_attempted': 0,
                'total_attempts': 0,
                'total_correct': 0,
                'avg_accuracy': 0
            }
            
            # MCQs due today
            cursor.execute("""
                SELECT COUNT(*) as mcqs_due
                FROM MCQ_Performance
                WHERE user_id = %s AND next_review_date <= CURDATE()
            """, (session['user_id'],))
            
            due_count = cursor.fetchone()
            
            return jsonify({
                'stats': {
                    'total_mcqs_attempted': overall['total_mcqs_attempted'] or 0,
                    'total_attempts': overall['total_attempts'] or 0,
                    'total_correct': overall['total_correct'] or 0,
                    'avg_accuracy': float(overall['avg_accuracy'] or 0),
                    'mcqs_due_today': due_count['mcqs_due'] or 0
                }
            }), 200
    
    except Error as e:
        logger.error(f"Get MCQ stats error: {e}")
        return jsonify({'error': 'Failed to fetch MCQ stats'}), 500


# ============================================================================
# HEALTH CHECK & ERROR HANDLERS
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        with get_db_connection() as conn:
            cursor = get_db_cursor(conn)
            cursor.execute("SELECT 1")
            cursor.fetchone()
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e)
        }), 503

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(Exception)
def handle_exception(error):
    """Handle unexpected exceptions"""
    logger.error(f"Unhandled exception: {error}")
    return jsonify({'error': 'An unexpected error occurred'}), 500

# ============================================================================
# RUN APPLICATION
# ============================================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    logger.info(f"Starting AutoRevise backend on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)