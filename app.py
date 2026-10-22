from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_wtf.csrf import CSRFProtect, CSRFError
from functools import wraps
from datetime import datetime, timedelta, date
import bcrypt
import secrets
import os
import re
import sys
import logging
import csv
import io
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from db_config import get_connection, get_db_connection, get_db_cursor
from achievement_system import check_and_unlock_achievements, VALID_SUBJECTS
from flashcard_system import (
    get_user_decks, create_deck, get_deck, delete_deck,
    get_deck_cards, create_card, update_card, delete_card, bulk_create_cards,
    get_study_cards, submit_card_review, get_user_stats, get_study_log,
    calculate_sm2
)

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Security Configuration from environment variables
_secret_key = os.getenv('SECRET_KEY')
if not _secret_key:
    # Fall back so a fresh clone without a .env still boots, but make it loud:
    # sessions signed with a known key can be forged.
    _secret_key = 'fallback-secret-key-for-development-only'
app.secret_key = _secret_key
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=int(os.getenv('SESSION_LIFETIME_DAYS', 7)))

# Session cookie hardening. SECURE defaults to False so local HTTP development
# keeps working; set SESSION_COOKIE_SECURE=True when serving over HTTPS.
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'

# Cap request bodies so a CSV upload cannot exhaust memory.
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_UPLOAD_MB', 5)) * 1024 * 1024

# Login throttling knobs (previously hardcoded, so these .env values did nothing).
LOGIN_ATTEMPTS_LIMIT = int(os.getenv('LOGIN_ATTEMPTS_LIMIT', 5))
LOGIN_ATTEMPTS_WINDOW_MINUTES = int(os.getenv('LOGIN_ATTEMPTS_WINDOW_MINUTES', 15))

# Previously magic numbers scattered through the queries below.
QUIZ_QUESTION_COUNT = int(os.getenv('QUIZ_QUESTION_COUNT', 20))
LEADERBOARD_SIZE = int(os.getenv('LEADERBOARD_SIZE', 50))

# CSRF Protection - enabled by default. Tokens are supplied by base.html's
# <meta name="csrf-token"> (read by fetch() callers) and by a hidden field in
# the login/register forms.
#
# CSRFProtect is initialised unconditionally so that csrf_token() always
# exists in Jinja; CSRF_ENABLED only controls *enforcement*. Initialising it
# conditionally would make every template that renders a token blow up with
# "'csrf_token' is undefined" whenever the feature was switched off.
csrf_enabled = os.getenv('CSRF_ENABLED', 'True').lower() == 'true'
app.config['WTF_CSRF_ENABLED'] = csrf_enabled
app.config['WTF_CSRF_TIME_LIMIT'] = None  # CSRF tokens don't expire
csrf = CSRFProtect(app)
if not csrf_enabled:
    app.logger.warning('CSRF protection is DISABLED (CSRF_ENABLED=False).')

# Configure logging
if not os.path.exists('logs'):
    os.makedirs('logs')

file_handler = RotatingFileHandler('logs/mcq_app.log', maxBytes=10240000, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('MCQ Application startup')

if not os.getenv('SECRET_KEY'):
    app.logger.warning(
        'SECRET_KEY is not set; using the insecure built-in fallback. '
        'Set SECRET_KEY in .env before deploying.'
    )


@app.context_processor
def inject_current_year():
    """Make the current year available to every template (used in the footer)."""
    return {'current_year': datetime.now().year}


# ---------------- AUTHENTICATION DECORATOR ----------------
def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or 'username' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or not session.get('is_admin', False):
            flash('Admin access required.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


# ---------------- UPLOAD VALIDATION ----------------
# Browsers report CSV files inconsistently, so accept the handful of types
# they actually send rather than trusting the filename alone.
ALLOWED_CSV_MIMETYPES = {
    'text/csv', 'text/plain', 'application/csv',
    'application/vnd.ms-excel', 'application/octet-stream',
}


def validate_csv_upload(file):
    """
    Validate an uploaded CSV. Returns an error string, or None if it's fine.

    Size is enforced by MAX_CONTENT_LENGTH (Flask aborts with 413 before the
    request body reaches here), so this only has to check the shape.
    """
    if not file or not file.filename:
        return 'No file provided'

    if not file.filename.lower().endswith('.csv'):
        return 'Invalid file. Must be a .csv file'

    if file.mimetype and file.mimetype not in ALLOWED_CSV_MIMETYPES:
        return f'Unsupported content type: {file.mimetype}. Expected a CSV file.'

    return None




# ---------------- AUTHENTICATION ROUTES ----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        full_name = request.form.get('full_name', '').strip()
        
        # Validation
        if not all([username, email, password, confirm_password, full_name]):
            flash('All fields are required!', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template('register.html')
        
        if len(password) < 8:
            flash('Password must be at least 8 characters long!', 'error')
            return render_template('register.html')

        if not (re.search(r'[A-Za-z]', password) and re.search(r'\d', password)):
            flash('Password must contain at least one letter and one number!', 'error')
            return render_template('register.html')

        if len(username) < 3:
            flash('Username must be at least 3 characters long!', 'error')
            return render_template('register.html')

        # Hash password and create user
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                # Check if username/email already exists. This is advisory
                # only - two concurrent registrations can both pass it, so the
                # UNIQUE constraint below is the real guard and a duplicate
                # key error is handled as a normal "already taken" outcome.
                cursor.execute(
                    'SELECT user_id FROM users WHERE username = %s OR email = %s',
                    (username, email)
                )
                if cursor.fetchone():
                    flash('Username or email already exists!', 'error')
                    return render_template('register.html')

                cursor.execute('''
                    INSERT INTO users (username, email, password_hash, full_name, is_admin, created_at)
                    VALUES (%s, %s, %s, %s, 0, NOW())
                ''', (username, email, password_hash, full_name))
                conn.commit()

                flash('Registration successful! Please login.', 'success')
                return redirect(url_for('login'))
            except Exception as e:
                conn.rollback()
                if getattr(e, 'errno', None) == 1062:
                    # Lost the race against a concurrent signup.
                    flash('Username or email already exists!', 'error')
                else:
                    app.logger.error('Registration failed for %r', username, exc_info=True)
                    flash('Registration failed. Please try again.', 'error')
                return render_template('register.html')
            finally:
                cursor.close()

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Username and password are required!', 'error')
            return render_template('login.html')
        
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                # Rate limiting check. Counted per (username, IP) so a single
                # attacker cannot lock a known username out for everyone by
                # deliberately failing logins against it.
                ip_address = request.remote_addr
                cursor.execute('''
                    SELECT COUNT(*) as attempts
                    FROM login_attempts
                    WHERE username = %s
                    AND ip_address = %s
                    AND success = 0
                    AND attempted_at > DATE_SUB(NOW(), INTERVAL %s MINUTE)
                ''', (username, ip_address, LOGIN_ATTEMPTS_WINDOW_MINUTES))

                attempts = cursor.fetchone()['attempts']

                if attempts >= LOGIN_ATTEMPTS_LIMIT:
                    flash(
                        'Too many failed login attempts. Please try again in '
                        f'{LOGIN_ATTEMPTS_WINDOW_MINUTES} minutes.', 'error'
                    )
                    return render_template('login.html')

                # Fetch user
                cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
                user = cursor.fetchone()

                if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                    # Successful login
                    cursor.execute('''
                        INSERT INTO login_attempts (username, ip_address, attempted_at, success)
                        VALUES (%s, %s, NOW(), 1)
                    ''', (username, ip_address))

                    # Create session
                    session['user_id'] = user['user_id']
                    session['username'] = user['username']
                    session['is_admin'] = user['is_admin']
                    session['full_name'] = user['full_name']
                    session.permanent = True

                    # Store session in database
                    session_id = secrets.token_urlsafe(32)
                    expires_at = datetime.now() + app.config['PERMANENT_SESSION_LIFETIME']

                    cursor.execute('''
                        INSERT INTO user_sessions (session_id, user_id, created_at, expires_at, ip_address)
                        VALUES (%s, %s, NOW(), %s, %s)
                    ''', (session_id, user['user_id'], expires_at, ip_address))

                    conn.commit()

                    flash(f'Welcome back, {user["full_name"]}!', 'success')
                    return redirect(url_for('index'))
                else:
                    # Failed login
                    cursor.execute('''
                        INSERT INTO login_attempts (username, ip_address, attempted_at, success)
                        VALUES (%s, %s, NOW(), 0)
                    ''', (username, ip_address))
                    conn.commit()

                    flash('Invalid username or password!', 'error')
                    return render_template('login.html')
            finally:
                cursor.close()

    return render_template('login.html')


@app.route('/logout')
def logout():
    user_id = session.get('user_id')

    if user_id:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Delete user sessions
            cursor.execute('DELETE FROM user_sessions WHERE user_id = %s', (user_id,))
            conn.commit()
            cursor.close()

    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('index'))


# ---------------- HOME PAGE ----------------
@app.route('/')
def index():
    return render_template('index.html')


# ---------------- QUIZ PAGE ----------------
@app.route('/quiz/<subject>')
@login_required
def quiz(subject):
    import random

    app.logger.info('Quiz page requested: subject=%r user_id=%s', subject, session.get('user_id'))

    # Track quiz start time
    session['quiz_start_time'] = datetime.now().isoformat()

    with get_db_cursor(dictionary=True) as cursor:
        # OPTIMIZED: Replace RAND() with efficient subquery approach
        # RAND() is O(n log n), this is O(n) + O(log n)
        # Step 1: Get total count and calculate offset
        cursor.execute(
            "SELECT COUNT(*) as total FROM questions WHERE subject=%s",
            (subject,)
        )
        total_questions = cursor.fetchone()['total']

        # Step 2: Get questions using indexed selection
        if total_questions > QUIZ_QUESTION_COUNT:
            # Pseudo-random offset so each visit gets a different slice.
            seed = random.randrange(total_questions)

            # Fetch using modulo-based selection (much faster than RAND())
            cursor.execute("""
                SELECT q.* FROM (
                    SELECT @row := @row + 1 as row_num, questions.*
                    FROM questions, (SELECT @row := 0) r
                    WHERE subject = %s
                    ORDER BY q_id
                ) q
                WHERE MOD(q.row_num + %s, %s) < %s
                LIMIT %s
            """, (subject, seed, total_questions, QUIZ_QUESTION_COUNT, QUIZ_QUESTION_COUNT))
        else:
            # If total questions <= the quiz size, just get all
            cursor.execute(
                "SELECT * FROM questions WHERE subject=%s ORDER BY q_id",
                (subject,)
            )

        questions = cursor.fetchall()

    # Shuffle in Python (much faster than DB RAND())
    random.shuffle(questions)

    app.logger.info('Loaded %s questions for subject=%r', len(questions), subject)
    session['quiz_subject'] = subject

    return render_template('quiz.html', questions=questions, subject=subject)


# ---------------- SAVE RESULT ----------------
def save_result_to_db(conn, user_id, subject, score, total):
    """Save result to database - OPTIMIZED to reuse connection"""
    cur = conn.cursor()
    percentage = round((score / total) * 100, 2) if total else 0.0
    cur.execute(
        "INSERT INTO results (user_id, subject, score, total_questions, percentage) VALUES (%s, %s, %s, %s, %s)",
        (user_id, subject, score, total, percentage)
    )
    result_id = cur.lastrowid  # Get the inserted result_id
    cur.close()
    return result_id


# ---------------- SAVE USER ANSWERS ----------------
def save_user_answers(conn, result_id, answers):
    """Save user's answers to database for review later - OPTIMIZED with batch insert"""
    if not answers:
        app.logger.info('No answers to save for result_id %s', result_id)
        return

    cur = conn.cursor()

    try:
        # Batch insert - much more efficient than loop
        values = [(result_id, int(q_id), answer) for q_id, answer in answers.items()]
        cur.executemany("""
            INSERT INTO user_answers (result_id, q_id, user_answer)
            VALUES (%s, %s, %s)
        """, values)

        app.logger.info('Saved %s user answers for result_id %s', len(answers), result_id)
    except Exception:
        app.logger.error('Error saving user answers for result_id %s', result_id, exc_info=True)
        raise  # Re-raise to handle in calling function
    finally:
        cur.close()


# ---------------- ACHIEVEMENT CHECKING SYSTEM ----------------
# Achievement logic has been refactored to achievement_system.py for better maintainability
# The check_and_unlock_achievements function is imported from that module


# ---------------- SUBMIT QUIZ ----------------
@app.route('/submit_quiz', methods=['POST'])
@login_required
def submit_quiz():
    quiz_end_time = datetime.now()  # Record when quiz was submitted

    data = request.get_json(force=True, silent=True) or {}

    answers = data.get('answers', {})
    subject = data.get('subject') or session.get('quiz_subject')
    user_id = session.get('user_id')  # Get from authenticated session
    quiz_start_time = session.get('quiz_start_time')  # Get start time from session

    if not isinstance(answers, dict):
        return jsonify({"error": "answers must be an object"}), 400

    if not subject:
        return jsonify({"error": "no subject supplied"}), 400

    # If start time not in session, estimate it (fallback)
    if not quiz_start_time:
        # Estimate: assume 2 minutes per question as default
        total_questions = len(answers)
        estimated_duration = timedelta(minutes=total_questions * 2)
        quiz_start_time = quiz_end_time - estimated_duration
    else:
        quiz_start_time = datetime.fromisoformat(quiz_start_time)

    app.logger.info(
        'Quiz submitted: user_id=%s subject=%r answers=%s duration=%.1fs',
        user_id, subject, len(answers),
        (quiz_end_time - quiz_start_time).total_seconds()
    )
    app.logger.debug('Submitted answers payload: %s', answers)

    qids = list(answers.keys())
    if not qids:
        return jsonify({"error": "no answers received"}), 400

    try:
        qids_int = [int(q) for q in qids]
    except (TypeError, ValueError):
        return jsonify({"error": "invalid question ids"}), 400

    placeholders = ','.join(['%s'] * len(qids_int))
    query = f"SELECT q_id, option_a, option_b, option_c, option_d, correct_option FROM questions WHERE q_id IN ({placeholders})"

    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    
    try:
        cur.execute(query, tuple(qids_int))
        rows = cur.fetchall()

        # Build correct answer map - OPTIMIZED text to letter conversion
        correct_map = {}
        for r in rows:
            qid = str(r['q_id'])
            correct_text = r['correct_option']
            # Efficient lookup using dict comprehension
            option_map = {
                r['option_a']: 'A',
                r['option_b']: 'B',
                r['option_c']: 'C',
                r['option_d']: 'D'
            }
            correct_map[qid] = option_map.get(correct_text)

        app.logger.debug('Correct answers map: %s', correct_map)

        # Calculate score
        score = 0
        for qid, given in answers.items():
            correct = correct_map.get(str(qid))
            if correct and str(given).strip().upper() == correct:
                score += 1

        total = len(qids_int)
        percentage = round((score / total) * 100, 2) if total else 0.0

        app.logger.info('Quiz scored: user_id=%s %s/%s (%s%%)', user_id, score, total, percentage)

        # Save to database - OPTIMIZED: single connection for all operations
        result_id = save_result_to_db(conn, user_id, subject, score, total)

        # Save user answers for later review
        save_user_answers(conn, result_id, answers)

        # Check and unlock achievements with timing data
        newly_unlocked = check_and_unlock_achievements(
            conn, user_id, subject, score, total, percentage,
            result_id, quiz_start_time, quiz_end_time
        )
        app.logger.info('Achievements checked: %s newly unlocked', len(newly_unlocked))

        # Commit all changes together
        conn.commit()

    except Exception:
        app.logger.error('Failed to save quiz submission for user %s', user_id, exc_info=True)
        conn.rollback()
        return jsonify({"error": "Could not save your quiz. Please try again."}), 500
    finally:
        cur.close()
        conn.close()

    # Save to session for result page
    session['last_result'] = {
        "score": score,
        "total": total,
        "percentage": percentage,
        "subject": subject,
        "newly_unlocked_achievements": [{"title": a["title"], "icon": a.get("icon", "🏆"), "description": a.get("description", "")} for a in newly_unlocked] if newly_unlocked else []
    }
    
    # Clear quiz start time from session
    session.pop('quiz_start_time', None)
    
    app.logger.debug('Stored last_result in session: %s', session['last_result'])

    return jsonify({"redirect": url_for('show_latest_result')})


# ---------------- SHOW LATEST RESULT ----------------
@app.route('/show_result')
@login_required
def show_latest_result():
    result = session.get('last_result')

    if not result:
        app.logger.info('No result in session; redirecting to index')
        return redirect(url_for('index'))

    return render_template('result.html', result=result)


# ---------------- MARK QUESTION ----------------
@app.route('/mark_question', methods=['POST'])
@login_required
def mark_question():
    data = request.get_json(silent=True) or {}
    user_id = session.get('user_id')  # Get from authenticated session

    # Validate before touching the DB - a missing/non-numeric q_id used to be
    # inserted as NULL without complaint.
    try:
        q_id = int(data['q_id'])
    except (KeyError, TypeError, ValueError):
        return jsonify({'error': 'A valid q_id is required.'}), 400

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO marked_questions (user_id, q_id)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE q_id = q_id
            """, (user_id, q_id))
            conn.commit()
            cursor.close()
        app.logger.info('Question %s marked by user %s', q_id, user_id)
        return jsonify({'message': 'Question marked successfully.', 'success': True})
    except Exception:
        app.logger.error(
            'Failed to mark question %s for user %s', q_id, user_id, exc_info=True
        )
        return jsonify({'error': 'Failed to mark question.'}), 500


# ---------------- VIEW ALL RESULTS ----------------
@app.route('/results')
@login_required
def view_results():
    user_id = session.get('user_id')  # Get from authenticated session
    with get_db_cursor(dictionary=True) as cur:
        cur.execute("""
            SELECT result_id, subject, score, total_questions, percentage, submitted_at
            FROM results
            WHERE user_id = %s
            ORDER BY submitted_at DESC
        """, (user_id,))
        results = cur.fetchall()
    return render_template('results.html', results=results)


# ---------------- VIEW ACHIEVEMENTS (COMPREHENSIVE) ----------------
@app.route('/achievements')
@login_required
def view_achievements():
    user_id = session.get('user_id')  # Get from authenticated session

    with get_db_cursor(dictionary=True) as cur:
        # Get all achievement definitions with category grouping
        cur.execute("""
            SELECT a.achievement_id, a.achievement_code, a.title, a.description,
                   a.icon, a.category, a.requirement_type, a.requirement_value, a.subject,
                   ua.unlocked_at, ua.progress_when_unlocked,
                   CASE WHEN ua.id IS NOT NULL THEN TRUE ELSE FALSE END as is_unlocked
            FROM achievements a
            LEFT JOIN user_achievements ua ON a.achievement_id = ua.achievement_id AND ua.user_id = %s
            ORDER BY a.category, a.achievement_id
        """, (user_id,))
        all_achievements = cur.fetchall()

        # Get comprehensive user statistics
        cur.execute("""
            SELECT * FROM user_statistics WHERE user_id = %s
        """, (user_id,))
        stats = cur.fetchone()

    if not stats:
        stats = {
            'total_quizzes_completed': 0,
            'total_questions_solved': 0,
            'total_correct_answers': 0,
            'perfect_quizzes_count': 0,
            'current_streak_days': 0,
            'longest_streak_days': 0,
            'consecutive_perfect_quizzes': 0,
            'max_consecutive_correct': 0,
            'night_owl_count': 0,
            'early_bird_count': 0,
            'incorrect_answers_reviewed': 0,
            'physics_quizzes': 0,
            'chemistry_quizzes': 0,
            'biology_quizzes': 0,
            'mathematics_quizzes': 0
        }
    
    # Calculate progress for each achievement
    for achievement in all_achievements:
        req_type = achievement['requirement_type']
        req_value = achievement['requirement_value'] or 1
        
        # Default values
        achievement['progress'] = 0
        achievement['progress_text'] = ""
        
        if achievement['is_unlocked']:
            achievement['progress'] = 100
            achievement['progress_text'] = "Unlocked!"
        else:
            # Calculate based on requirement type
            if req_type == 'total_quizzes':
                current = stats['total_quizzes_completed']
                achievement['progress'] = min(100, int((current / req_value) * 100))
                achievement['progress_text'] = f"{current}/{req_value} quizzes"
                
            elif req_type == 'total_questions':
                current = stats['total_questions_solved']
                achievement['progress'] = min(100, int((current / req_value) * 100))
                achievement['progress_text'] = f"{current}/{req_value} questions"
                
            elif req_type == 'first_quiz_any':
                current = 1 if stats['total_quizzes_completed'] > 0 else 0
                achievement['progress'] = current * 100
                achievement['progress_text'] = "Complete your first quiz"
                
            elif req_type == 'first_quiz_subject':
                # subject is nullable in the achievements table, so guard it
                subj = (achievement['subject'] or '').lower()
                current = 1 if (stats.get(f'{subj}_quizzes') or 0) > 0 else 0
                achievement['progress'] = current * 100
                achievement['progress_text'] = f"Complete first {achievement['subject']} quiz"
                
            elif req_type == 'all_subjects_once':
                completed = sum([1 for s in ['physics', 'chemistry', 'biology', 'mathematics'] 
                               if stats.get(f'{s}_quizzes', 0) > 0])
                achievement['progress'] = int((completed / 4) * 100)
                achievement['progress_text'] = f"{completed}/4 subjects"
                
            elif req_type == 'subject_dedication':
                max_subject = max([stats.get(f'{s}_quizzes', 0) 
                                  for s in ['physics', 'chemistry', 'biology', 'mathematics']])
                achievement['progress'] = min(100, int((max_subject / req_value) * 100))
                achievement['progress_text'] = f"{max_subject}/{req_value} in one subject"
                
            elif req_type == 'perfect_once':
                current = min(1, stats['perfect_quizzes_count'])
                achievement['progress'] = current * 100
                achievement['progress_text'] = "Score 100% once"
                
            elif req_type == 'perfect_all_subjects':
                completed = sum([1 for s in ['physics', 'chemistry', 'biology', 'mathematics'] 
                               if stats.get(f'{s}_perfect_count', 0) > 0])
                achievement['progress'] = int((completed / 4) * 100)
                achievement['progress_text'] = f"{completed}/4 subjects perfect"
                
            elif req_type == 'consecutive_90_plus':
                # This is tracked separately in achievement checking
                achievement['progress'] = 0
                achievement['progress_text'] = "Keep scoring 90%+"
                
            elif req_type == 'consecutive_correct':
                current = stats['max_consecutive_correct']
                achievement['progress'] = min(100, int((current / req_value) * 100))
                achievement['progress_text'] = f"{current}/{req_value} consecutive correct"
                
            elif req_type == 'fast_completion':
                achievement['progress'] = 0
                achievement['progress_text'] = "Complete quiz under 1 min/question"
                
            elif req_type == 'night_quiz':
                current = min(1, stats['night_owl_count'])
                achievement['progress'] = current * 100
                achievement['progress_text'] = "Quiz between 12 AM - 5 AM"
                
            elif req_type == 'early_quiz':
                current = min(1, stats['early_bird_count'])
                achievement['progress'] = current * 100
                achievement['progress_text'] = "Quiz before 8 AM"
                
            elif req_type == 'daily_streak':
                current = stats['current_streak_days']
                achievement['progress'] = min(100, int((current / req_value) * 100))
                achievement['progress_text'] = f"{current}/{req_value} days streak"
                
            elif req_type == 'score_improvement':
                achievement['progress'] = 0
                achievement['progress_text'] = "Improve by 20%+"
                
            elif req_type == 'quiz_retries':
                achievement['progress'] = 0
                achievement['progress_text'] = "Retry and improve"
                
            elif req_type == 'review_mistakes':
                current = stats['incorrect_answers_reviewed']
                achievement['progress'] = min(100, int((current / req_value) * 100))
                achievement['progress_text'] = f"{current}/{req_value} mistakes reviewed"
                
            elif req_type == 'quiz_marathon':
                achievement['progress'] = 0
                achievement['progress_text'] = "5 quizzes in one sitting"
    
    # Group achievements by category
    achievements_by_category = {}
    for achievement in all_achievements:
        category = achievement['category']
        if category not in achievements_by_category:
            achievements_by_category[category] = []
        achievements_by_category[category].append(achievement)
    
    # Count unlocked achievements
    unlocked_count = sum(1 for a in all_achievements if a['is_unlocked'])
    total_count = len(all_achievements)
    completion_percentage = int((unlocked_count / total_count) * 100) if total_count > 0 else 0

    return render_template('achievements.html',
                         achievements=all_achievements,
                         achievements_by_category=achievements_by_category,
                         stats=stats,
                         unlocked_count=unlocked_count,
                         total_count=total_count,
                         completion_percentage=completion_percentage)



# ---------------- REVIEW QUIZ - VIEW ALL QUESTIONS & ANSWERS ----------------
@app.route('/review_quiz/<int:result_id>')
@login_required
def review_quiz(result_id):
    user_id = session.get('user_id')  # Get from authenticated session

    try:
        with get_db_connection() as conn:
            cur = conn.cursor(dictionary=True)
            try:
                # Get result details
                cur.execute("""
                    SELECT subject, score, total_questions, percentage, submitted_at
                    FROM results
                    WHERE result_id = %s AND user_id = %s
                """, (result_id, user_id))
                result = cur.fetchone()

                if not result:
                    return redirect(url_for('view_results'))

                # Track review for achievement
                incorrect_count = result['total_questions'] - result['score']
                if incorrect_count > 0:
                    cur.execute("""
                        INSERT INTO user_statistics (user_id, total_reviews, incorrect_answers_reviewed)
                        VALUES (%s, 1, %s)
                        ON DUPLICATE KEY UPDATE
                            total_reviews = total_reviews + 1,
                            incorrect_answers_reviewed = incorrect_answers_reviewed + %s
                    """, (user_id, incorrect_count, incorrect_count))

                    # Check for Error Learner achievement
                    cur.execute(
                        "SELECT incorrect_answers_reviewed FROM user_statistics WHERE user_id = %s",
                        (user_id,)
                    )
                    stats = cur.fetchone()
                    if stats and (stats['incorrect_answers_reviewed'] or 0) >= 50:
                        cur.execute("""
                            INSERT IGNORE INTO user_achievements (user_id, achievement_id)
                            SELECT %s, achievement_id FROM achievements WHERE achievement_code = 'error_learner'
                        """, (user_id,))

                    conn.commit()

                # Get ALL questions from this quiz with user's answers
                cur.execute("""
                    SELECT q.q_id, q.question_text, q.option_a, q.option_b,
                           q.option_c, q.option_d, q.correct_option, q.subject,
                           ua.user_answer
                    FROM user_answers ua
                    JOIN questions q ON ua.q_id = q.q_id
                    WHERE ua.result_id = %s
                    ORDER BY q.q_id
                """, (result_id,))
                quiz_questions = cur.fetchall()

                # If no user answers found (old quiz), try to get questions by subject
                if not quiz_questions:
                    app.logger.info('No stored answers for result_id %s; falling back to subject', result_id)
                    cur.execute("""
                        SELECT q.q_id, q.question_text, q.option_a, q.option_b,
                               q.option_c, q.option_d, q.correct_option, q.subject,
                               NULL as user_answer
                        FROM questions q
                        WHERE q.subject = %s
                        LIMIT %s
                    """, (result['subject'], QUIZ_QUESTION_COUNT))
                    quiz_questions = cur.fetchall()
            finally:
                cur.close()

        app.logger.info('Review for result_id %s: %s questions', result_id, len(quiz_questions))

        return render_template('quiz_review.html',
                             result=result,
                             quiz_questions=quiz_questions,
                             result_id=result_id)

    except Exception:
        app.logger.error('Error in review_quiz for result_id %s', result_id, exc_info=True)
        flash('Could not load that quiz review.', 'error')
        return redirect(url_for('view_results'))


# ---------------- ADMIN PAGE ----------------
@app.route('/admin')
@admin_required
def admin():
    return render_template('admin.html')


# Fields every question write must supply.
QUESTION_FIELDS = (
    'question_text', 'option_a', 'option_b', 'option_c',
    'option_d', 'correct_option', 'subject'
)


def _validate_question_payload(data):
    """
    Pull the question fields out of a request body.

    Returns (values, error). Previously these routes indexed the dict directly,
    so a missing field raised KeyError and surfaced as an opaque 500.
    """
    if not isinstance(data, dict):
        return None, 'Expected a JSON object.'

    missing = [f for f in QUESTION_FIELDS if not str(data.get(f) or '').strip()]
    if missing:
        return None, f"Missing required field(s): {', '.join(missing)}"

    return [str(data[f]).strip() for f in QUESTION_FIELDS], None


# ---------------- API: CREATE QUESTION ----------------
@app.route('/api/questions', methods=['POST'])
@admin_required
def create_question():
    values, error = _validate_question_payload(request.get_json(silent=True))
    if error:
        return jsonify({"error": error}), 400

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO questions (question_text, option_a, option_b, option_c, option_d, correct_option, subject)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, tuple(values))
            conn.commit()
            cursor.close()
        return jsonify({"message": "Question added successfully"}), 201
    except Exception:
        app.logger.error('Failed to create question', exc_info=True)
        return jsonify({"error": "Could not add the question."}), 500


# ---------------- API: READ ALL QUESTIONS ----------------
@app.route('/api/questions', methods=['GET'])
@admin_required
def get_all_questions():
    subject = request.args.get('subject')
    try:
        with get_db_cursor(dictionary=True) as cursor:
            if subject:
                cursor.execute("SELECT * FROM questions WHERE subject = %s", (subject,))
            else:
                cursor.execute("SELECT * FROM questions")
            questions = cursor.fetchall()
        return jsonify(questions), 200
    except Exception:
        app.logger.error('Failed to list questions', exc_info=True)
        return jsonify({"error": "Could not load questions."}), 500


# ---------------- API: READ SINGLE QUESTION ----------------
@app.route('/api/questions/<int:qid>', methods=['GET'])
@admin_required
def get_question(qid):
    try:
        with get_db_cursor(dictionary=True) as cursor:
            cursor.execute("SELECT * FROM questions WHERE q_id = %s", (qid,))
            question = cursor.fetchone()
        if question:
            return jsonify(question), 200
        return jsonify({"error": "Question not found"}), 404
    except Exception:
        app.logger.error('Failed to load question %s', qid, exc_info=True)
        return jsonify({"error": "Could not load the question."}), 500


# ---------------- API: UPDATE QUESTION ----------------
@app.route('/api/questions/<int:qid>', methods=['PUT'])
@admin_required
def update_question(qid):
    values, error = _validate_question_payload(request.get_json(silent=True))
    if error:
        return jsonify({"error": error}), 400

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE questions
                SET question_text=%s, option_a=%s, option_b=%s, option_c=%s,
                    option_d=%s, correct_option=%s, subject=%s
                WHERE q_id=%s
            """, tuple(values) + (qid,))
            conn.commit()
            updated = cursor.rowcount
            cursor.close()
        if updated == 0:
            return jsonify({"error": "Question not found"}), 404
        return jsonify({"message": "Question updated successfully"}), 200
    except Exception:
        app.logger.error('Failed to update question %s', qid, exc_info=True)
        return jsonify({"error": "Could not update the question."}), 500


# ---------------- API: DELETE QUESTION ----------------
@app.route('/api/questions/<int:qid>', methods=['DELETE'])
@admin_required
def delete_question(qid):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM questions WHERE q_id = %s", (qid,))
            conn.commit()
            deleted = cursor.rowcount
            cursor.close()
        if deleted == 0:
            return jsonify({"error": "Question not found"}), 404
        return jsonify({"message": "Question deleted successfully"}), 200
    except Exception:
        app.logger.error('Failed to delete question %s', qid, exc_info=True)
        return jsonify({"error": "Could not delete the question."}), 500


# ---------------- SECURITY HEADERS ----------------
@app.after_request
def set_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response


# ============================================================================
# FLASHCARD SYSTEM ROUTES
# ============================================================================

# ---------------- FLASHCARD DASHBOARD ----------------
@app.route('/flashcards')
@login_required
def flashcard_dashboard():
    """Flashcard dashboard showing decks and study stats"""
    user_id = session.get('user_id')
    decks = get_user_decks(user_id)
    stats = get_user_stats(user_id)
    return render_template('flashcard_dashboard.html', decks=decks, stats=stats)


# ---------------- DECK ROUTES ----------------
@app.route('/decks', methods=['GET'])
@login_required
def list_decks():
    """Get all decks for logged-in user"""
    user_id = session.get('user_id')
    decks = get_user_decks(user_id)
    return jsonify({'decks': decks}), 200


@app.route('/decks', methods=['POST'])
@login_required
def api_create_deck():
    """Create a new deck"""
    data = request.get_json()
    deck_name = data.get('deck_name', '').strip()
    description = data.get('description', '').strip()
    
    if not deck_name:
        return jsonify({'error': 'Deck name is required'}), 400
    
    user_id = session.get('user_id')
    deck_id = create_deck(user_id, deck_name, description)
    
    return jsonify({
        'message': 'Deck created successfully',
        'deck_id': deck_id,
        'deck_name': deck_name
    }), 201


@app.route('/decks/<int:deck_id>')
@login_required
def view_deck(deck_id):
    """View a specific deck with its cards"""
    user_id = session.get('user_id')
    deck = get_deck(deck_id, user_id)
    
    if not deck:
        flash('Deck not found', 'error')
        return redirect(url_for('flashcard_dashboard'))
    
    cards = get_deck_cards(deck_id, user_id)
    return render_template('deck_view.html', deck=deck, cards=cards)


@app.route('/decks/<int:deck_id>/delete', methods=['POST'])
@login_required
def api_delete_deck(deck_id):
    """Delete a deck"""
    user_id = session.get('user_id')
    success = delete_deck(deck_id, user_id)
    
    if success:
        return jsonify({'message': 'Deck deleted successfully'}), 200
    return jsonify({'error': 'Deck not found or unauthorized'}), 404


# ---------------- CARD ROUTES ----------------
@app.route('/decks/<int:deck_id>/cards', methods=['GET'])
@login_required
def get_cards(deck_id):
    """Get all cards in a deck"""
    user_id = session.get('user_id')
    cards = get_deck_cards(deck_id, user_id)
    return jsonify({'cards': cards}), 200


@app.route('/decks/<int:deck_id>/cards', methods=['POST'])
@login_required
def api_create_card(deck_id):
    """Create a new card in a deck"""
    data = request.get_json()
    front_content = data.get('front_content', '').strip()
    back_content = data.get('back_content', '').strip()
    
    if not front_content or not back_content:
        return jsonify({'error': 'Both front and back content are required'}), 400
    
    user_id = session.get('user_id')
    card_id = create_card(deck_id, user_id, front_content, back_content)
    
    if card_id:
        return jsonify({
            'message': 'Card created successfully',
            'card_id': card_id
        }), 201
    return jsonify({'error': 'Failed to create card'}), 400


@app.route('/cards/<int:card_id>', methods=['PUT'])
@login_required
def api_update_card(card_id):
    """Update a card"""
    data = request.get_json()
    front_content = data.get('front_content', '').strip()
    back_content = data.get('back_content', '').strip()
    
    if not front_content or not back_content:
        return jsonify({'error': 'Both front and back content are required'}), 400
    
    user_id = session.get('user_id')
    success = update_card(card_id, user_id, front_content, back_content)
    
    if success:
        return jsonify({'message': 'Card updated successfully'}), 200
    return jsonify({'error': 'Card not found or unauthorized'}), 404


@app.route('/cards/<int:card_id>', methods=['DELETE'])
@login_required
def api_delete_card(card_id):
    """Delete a card"""
    user_id = session.get('user_id')
    success = delete_card(card_id, user_id)
    
    if success:
        return jsonify({'message': 'Card deleted successfully'}), 200
    return jsonify({'error': 'Card not found or unauthorized'}), 404


@app.route('/decks/<int:deck_id>/upload-cards', methods=['POST'])
@login_required
def upload_cards_bulk(deck_id):
    """Bulk upload cards from JSON data"""
    data = request.get_json()
    cards_data = data.get('cards', [])
    
    if not cards_data:
        return jsonify({'error': 'No cards provided'}), 400
    
    user_id = session.get('user_id')
    result = bulk_create_cards(deck_id, user_id, cards_data)
    
    return jsonify({
        'message': f"Successfully added {result['inserted']} card(s)",
        'inserted': result['inserted'],
        'failed': result['failed'],
        'errors': result['errors']
    }), 201 if result['inserted'] > 0 else 400


@app.route('/decks/<int:deck_id>/upload-csv', methods=['POST'])
@login_required
def upload_flashcard_csv(deck_id):
    """Upload flashcards from CSV file (Question,Answer format)"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']

    error = validate_csv_upload(file)
    if error:
        return jsonify({'error': error}), 400

    user_id = session.get('user_id')

    try:
        # Read CSV file
        stream = io.StringIO(file.stream.read().decode("UTF-8"), newline=None)
        csv_reader = csv.DictReader(stream)

        cards_data = []
        for row in csv_reader:
            cards_data.append(row)

        if not cards_data:
            return jsonify({'error': 'CSV file is empty'}), 400

        # Import cards using bulk_create_cards
        result = bulk_create_cards(deck_id, user_id, cards_data)

        return jsonify({
            'message': f"Successfully imported {result['inserted']} card(s)",
            'inserted': result['inserted'],
            'failed': result['failed'],
            'errors': result['errors']
        }), 200 if result['failed'] == 0 else 207

    except UnicodeDecodeError:
        return jsonify({'error': 'File must be UTF-8 encoded text.'}), 400
    except Exception:
        app.logger.error('Error uploading flashcard CSV to deck %s', deck_id, exc_info=True)
        return jsonify({'error': 'Upload failed. Please check the file and try again.'}), 500


# ---------------- STUDY SESSION ROUTES ----------------
@app.route('/study')
@login_required
def study_session_page():
    """Study session page"""
    deck_id = request.args.get('deck_id', type=int)
    user_id = session.get('user_id')
    
    cards = get_study_cards(user_id, deck_id, limit=20)
    
    if not cards:
        flash('No cards due for review!', 'info')
        return redirect(url_for('flashcard_dashboard'))
    
    deck_name = cards[0]['deck_name'] if cards and deck_id else 'All Decks'
    # The template shows a "Day Streak" tile from stats; without this it
    # silently rendered 0 for everyone.
    stats = get_user_stats(user_id)
    return render_template('study_session.html', cards=cards, deck_name=deck_name,
                           deck_id=deck_id, stats=stats)


@app.route('/study-session', methods=['GET'])
@login_required
def get_study_session():
    """API: Get cards due for review"""
    deck_id = request.args.get('deck_id', type=int)
    limit = request.args.get('limit', default=20, type=int)
    user_id = session.get('user_id')
    
    cards = get_study_cards(user_id, deck_id, limit)
    
    return jsonify({
        'cards': cards,
        'total': len(cards)
    }), 200


@app.route('/submit-review', methods=['POST'])
@login_required
def submit_review():
    """Submit a card review"""
    data = request.get_json()
    card_id = data.get('card_id')
    rating = data.get('rating')
    
    if not card_id or not rating:
        return jsonify({'error': 'card_id and rating are required'}), 400
    
    if rating not in ['forgot', 'hard', 'good', 'easy']:
        return jsonify({'error': 'Invalid rating'}), 400
    
    user_id = session.get('user_id')
    result = submit_card_review(user_id, card_id, rating)
    
    if result:
        return jsonify({
            'message': 'Review submitted successfully',
            **result
        }), 200
    return jsonify({'error': 'Failed to submit review'}), 400


# ---------------- FLASHCARD STATS ----------------
@app.route('/flashcard-stats', methods=['GET'])
@login_required
def get_flashcard_stats():
    """Get user's flashcard statistics"""
    user_id = session.get('user_id')
    stats = get_user_stats(user_id)
    return jsonify({'stats': stats}), 200


@app.route('/study-log', methods=['GET'])
@login_required
def get_study_log_api():
    """Get user's study log"""
    limit = request.args.get('limit', default=30, type=int)
    user_id = session.get('user_id')
    logs = get_study_log(user_id, limit)
    return jsonify({'logs': logs}), 200


# ============================================================================
# MCQ CATEGORY ROUTES
# ============================================================================

@app.route('/mcq-categories')
@login_required
def mcq_categories_page():
    """MCQ categories browsing page"""
    user_id = session.get('user_id')

    with get_db_cursor(dictionary=True) as cursor:
        cursor.execute("""
            SELECT c.*, COUNT(q.q_id) AS question_count
            FROM mcq_categories c
            LEFT JOIN questions q ON c.category_id = q.category_id
            GROUP BY c.category_id
            ORDER BY c.category_name
        """)
        categories = cursor.fetchall()

        # Get user stats
        cursor.execute("""
            SELECT
                COALESCE(SUM(total_questions), 0) as total_attempted,
                COALESCE(SUM(score), 0) as correct_answers,
                CASE
                    WHEN COALESCE(SUM(total_questions), 0) > 0
                    THEN (COALESCE(SUM(score), 0) * 100.0 / SUM(total_questions))
                    ELSE 0
                END as accuracy
            FROM results WHERE user_id = %s
        """, (user_id,))
        quiz_stats = cursor.fetchone()

        cursor.execute("SELECT COALESCE(points, 0) as points FROM users WHERE user_id = %s", (user_id,))
        user_row = cursor.fetchone()

    user_stats = {
        'total_attempted': quiz_stats['total_attempted'] if quiz_stats else 0,
        'correct_answers': quiz_stats['correct_answers'] if quiz_stats else 0,
        'accuracy': quiz_stats['accuracy'] if quiz_stats else 0,
        'points': user_row['points'] if user_row else 0
    }

    return render_template('mcq_categories.html', categories=categories, user_stats=user_stats)


@app.route('/mcq/categories', methods=['GET'])
@login_required
def get_mcq_categories():
    """API: Get all MCQ categories"""
    with get_db_cursor(dictionary=True) as cursor:
        cursor.execute("""
            SELECT c.category_id, c.category_name, c.description, c.icon, c.color,
                   COUNT(q.q_id) AS question_count
            FROM mcq_categories c
            LEFT JOIN questions q ON c.category_id = q.category_id
            GROUP BY c.category_id
            ORDER BY c.category_name
        """)
        categories = cursor.fetchall()

    return jsonify({'categories': categories}), 200


@app.route('/mcq/category/<int:category_id>')
@login_required
def mcq_by_category(category_id):
    """Practice MCQs by category"""
    with get_db_cursor(dictionary=True) as cursor:
        # Get category info
        cursor.execute("""
            SELECT * FROM mcq_categories WHERE category_id = %s
        """, (category_id,))
        category = cursor.fetchone()

        if not category:
            flash('Category not found', 'error')
            return redirect(url_for('mcq_categories_page'))

        # Get questions for this category (random selection)
        cursor.execute("""
            SELECT q_id, question_text, option_a, option_b, option_c, option_d,
                   correct_option, difficulty
            FROM questions
            WHERE category_id = %s
            ORDER BY RAND()
            LIMIT %s
        """, (category_id, QUIZ_QUESTION_COUNT))
        questions = cursor.fetchall()

    if not questions:
        flash('No questions available in this category', 'info')
        return redirect(url_for('mcq_categories_page'))
    
    # Store in session for the quiz
    session['quiz_subject'] = category['category_name']
    session['quiz_start_time'] = datetime.now().isoformat()
    
    return render_template('quiz.html', questions=questions, subject=category['category_name'])


@app.route('/mcq/upload', methods=['POST'])
@admin_required
def upload_mcq_csv():
    """Admin: Upload MCQs from CSV file"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']

    error = validate_csv_upload(file)
    if error:
        return jsonify({'error': error}), 400

    category_id = request.form.get('category_id', type=int)

    try:
        stream = io.StringIO(file.stream.read().decode("UTF-8"), newline=None)
        csv_reader = csv.DictReader(stream)

        with get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                successful = 0
                failed = 0
                errors = []

                # Resolve category names up front instead of issuing a lookup
                # per row (the old behaviour was one extra query per question).
                category_lookup = {}
                if not category_id:
                    cursor.execute("SELECT category_id, category_name FROM mcq_categories")
                    category_lookup = {
                        name.strip().lower(): cid for cid, name in cursor.fetchall()
                    }

                for row_num, row in enumerate(csv_reader, start=2):
                    try:
                        question_text = (row.get('question_text') or '').strip()
                        option_a = (row.get('option_a') or '').strip()
                        option_b = (row.get('option_b') or '').strip()
                        option_c = (row.get('option_c') or '').strip()
                        option_d = (row.get('option_d') or '').strip()
                        correct_option = (row.get('correct_option') or '').strip()
                        subject = (row.get('subject') or '').strip()
                        difficulty = (row.get('difficulty') or 'medium').strip().lower()

                        if not all([question_text, option_a, option_b, option_c, option_d, correct_option]):
                            raise ValueError("Missing required fields")

                        # Use category from form or match on the subject name
                        final_category_id = category_id
                        if not final_category_id and subject:
                            final_category_id = category_lookup.get(subject.lower())

                        cursor.execute("""
                            INSERT INTO questions
                            (question_text, option_a, option_b, option_c, option_d,
                             correct_option, subject, category_id, difficulty)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (question_text, option_a, option_b, option_c, option_d,
                              correct_option, subject, final_category_id, difficulty))
                        successful += 1

                    except Exception as e:
                        failed += 1
                        app.logger.warning('MCQ CSV row %s failed', row_num, exc_info=True)
                        errors.append({
                            'row': row_num,
                            'error': str(e) if isinstance(e, ValueError) else 'Could not import this row'
                        })

                conn.commit()
            finally:
                cursor.close()

        return jsonify({
            'message': f'Upload complete: {successful} successful, {failed} failed',
            'successful': successful,
            'failed': failed,
            'errors': errors[:10]
        }), 200 if failed == 0 else 207

    except UnicodeDecodeError:
        return jsonify({'error': 'File must be UTF-8 encoded text.'}), 400
    except Exception:
        app.logger.error('MCQ CSV upload failed', exc_info=True)
        return jsonify({'error': 'Upload failed. Please check the file and try again.'}), 500


# ============================================================================
# POINTS AND LEADERBOARD
# ============================================================================

@app.route('/leaderboard')
@login_required
def leaderboard():
    """View the points leaderboard"""
    user_id = session.get('user_id')

    with get_db_cursor(dictionary=True) as cursor:
        cursor.execute("""
            SELECT u.user_id, u.username, u.full_name, COALESCE(u.points, 0) as points,
                   COUNT(DISTINCT ua.achievement_id) AS achievements_count,
                   COUNT(DISTINCT qr.result_id) AS quizzes_taken,
                   CASE WHEN COUNT(DISTINCT qr.result_id) > 0
                       THEN AVG(qr.score / qr.total_questions * 100)
                       ELSE 0
                   END AS avg_score
            FROM users u
            LEFT JOIN user_achievements ua ON u.user_id = ua.user_id
            LEFT JOIN results qr ON u.user_id = qr.user_id
            GROUP BY u.user_id
            ORDER BY u.points DESC
            LIMIT %s
        """, (LEADERBOARD_SIZE,))
        leaderboard_data = cursor.fetchall()

        # Get current user's rank and points
        cursor.execute("""
            SELECT COUNT(*) + 1 AS user_rank
            FROM users
            WHERE COALESCE(points, 0) > (SELECT COALESCE(points, 0) FROM users WHERE user_id = %s)
        """, (user_id,))
        rank_row = cursor.fetchone()
        user_rank = rank_row['user_rank'] if rank_row else None

        cursor.execute("SELECT COALESCE(points, 0) as points FROM users WHERE user_id = %s", (user_id,))
        points_row = cursor.fetchone()
        user_points = points_row['points'] if points_row else 0

    return render_template('leaderboard.html',
                          leaderboard=leaderboard_data, 
                          current_user_rank=user_rank,
                          current_user_points=user_points)


@app.route('/api/user-points', methods=['GET'])
@login_required
def get_user_points():
    """Get current user's points"""
    user_id = session.get('user_id')

    with get_db_cursor(dictionary=True) as cursor:
        cursor.execute("SELECT points FROM users WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()

    return jsonify({'points': (result['points'] if result else 0) or 0}), 200


# ---------------- ERROR HANDLERS ----------------
@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    app.logger.warning(f'404 error: {request.url}')
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    app.logger.error(f'500 error: {error}')
    return render_template('500.html'), 500


@app.errorhandler(403)
def forbidden_error(error):
    """Handle 403 errors"""
    app.logger.warning(f'403 error: {request.url}')
    return render_template('403.html'), 403


@app.errorhandler(413)
def payload_too_large(error):
    """Handle uploads over MAX_CONTENT_LENGTH"""
    limit_mb = app.config['MAX_CONTENT_LENGTH'] // (1024 * 1024)
    return jsonify({'error': f'File too large. Maximum size is {limit_mb} MB.'}), 413


@app.errorhandler(CSRFError)
def handle_csrf_error(error):
    """
    A missing/expired CSRF token is a normal condition (stale tab, restarted
    server), so explain it instead of surfacing a bare 400.
    """
    app.logger.warning('CSRF validation failed on %s: %s', request.path, error.description)
    if request.path.startswith('/api/') or request.is_json:
        return jsonify({'error': 'Your session expired. Please reload the page and try again.'}), 400
    flash('Your session expired. Please try again.', 'error')
    return redirect(request.referrer or url_for('index'))


# ---------------- MAIN ----------------
if __name__ == '__main__':
    # Use environment variable for debug mode
    debug_mode = os.getenv('FLASK_ENV', 'production') == 'development'
    app.run(debug=debug_mode)






