"""
Flashcard System Module
Implements flashcard deck management, spaced repetition (SM-2), and study sessions
"""

from datetime import datetime, timedelta, date
from db_config import get_connection


# ============================================================================
# SM-2 SPACED REPETITION ALGORITHM
# ============================================================================

def calculate_sm2(rating, current_interval, current_ease, repetitions):
    """
    SM-2 Spaced Repetition Algorithm
    
    Parameters:
    - rating: 'forgot', 'hard', 'good', 'easy'
    - current_interval: current interval in days
    - current_ease: current ease factor (1.3 - 2.5)
    - repetitions: number of successful repetitions
    
    Returns: (new_interval, new_ease, new_repetitions)
    """
    # Rating to quality mapping (0-5 scale for SM-2)
    quality_map = {
        'forgot': 0,  # Complete blackout
        'hard': 3,    # Correct response with serious difficulty
        'good': 4,    # Correct response with some hesitation
        'easy': 5     # Perfect response
    }
    
    quality = quality_map.get(rating, 3)
    
    # Calculate new ease factor
    new_ease = current_ease + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    new_ease = max(1.3, min(2.5, new_ease))  # Clamp between 1.3 and 2.5
    
    # Calculate new interval and repetitions
    if quality < 3:
        # Failed - reset
        new_interval = 1
        new_repetitions = 0
    else:
        # Success - increase interval
        new_repetitions = repetitions + 1
        if new_repetitions == 1:
            new_interval = 1
        elif new_repetitions == 2:
            new_interval = 6
        else:
            new_interval = round(current_interval * new_ease)
    
    # Cap maximum interval at 365 days
    new_interval = min(new_interval, 365)
    
    return new_interval, round(new_ease, 2), new_repetitions


def get_review_intervals(rating):
    """Get human-readable interval descriptions for UI"""
    intervals = {
        'forgot': '< 1 min',
        'hard': '< 10 min',
        'good': '1 day',
        'easy': '4 days'
    }
    return intervals.get(rating, '1 day')


# ============================================================================
# DECK MANAGEMENT
# ============================================================================

def get_user_decks(user_id):
    """Get all decks for a user with card counts"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT 
            d.deck_id,
            d.deck_name,
            d.description,
            d.created_at,
            COUNT(c.card_id) AS card_count,
            SUM(CASE WHEN cp.next_review_date <= CURDATE() THEN 1 ELSE 0 END) AS cards_due,
            SUM(CASE WHEN cp.next_review_date IS NULL THEN 1 ELSE 0 END) AS new_cards
        FROM decks d
        LEFT JOIN cards c ON d.deck_id = c.deck_id
        LEFT JOIN card_performance cp ON c.card_id = cp.card_id AND cp.user_id = %s
        WHERE d.user_id = %s
        GROUP BY d.deck_id
        ORDER BY d.created_at DESC
    """, (user_id, user_id))
    
    decks = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return decks


def create_deck(user_id, deck_name, description=''):
    """Create a new deck for a user"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO decks (user_id, deck_name, description) VALUES (%s, %s, %s)",
        (user_id, deck_name, description)
    )
    deck_id = cursor.lastrowid
    
    # Update user statistics
    cursor.execute("""
        INSERT INTO user_statistics (user_id, total_decks)
        VALUES (%s, 1)
        ON DUPLICATE KEY UPDATE total_decks = total_decks + 1
    """, (user_id,))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    # Check for deck achievements
    check_deck_achievements(user_id)
    
    return deck_id


def get_deck(deck_id, user_id):
    """Get a specific deck"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT d.*, COUNT(c.card_id) AS card_count
        FROM decks d
        LEFT JOIN cards c ON d.deck_id = c.deck_id
        WHERE d.deck_id = %s AND d.user_id = %s
        GROUP BY d.deck_id
    """, (deck_id, user_id))
    
    deck = cursor.fetchone()
    cursor.close()
    conn.close()
    
    return deck


def delete_deck(deck_id, user_id):
    """Delete a deck (owner only)"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Verify ownership
    cursor.execute("SELECT user_id FROM decks WHERE deck_id = %s", (deck_id,))
    deck = cursor.fetchone()
    
    if not deck or deck['user_id'] != user_id:
        cursor.close()
        conn.close()
        return False
    
    cursor.execute("DELETE FROM decks WHERE deck_id = %s", (deck_id,))
    
    # Update statistics
    cursor.execute("""
        UPDATE user_statistics 
        SET total_decks = GREATEST(0, total_decks - 1)
        WHERE user_id = %s
    """, (user_id,))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return True


# ============================================================================
# CARD MANAGEMENT
# ============================================================================

def get_deck_cards(deck_id, user_id):
    """Get all cards in a deck with performance data"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT 
            c.card_id,
            c.front_content,
            c.back_content,
            c.created_at,
            cp.next_review_date,
            cp.interval_days,
            cp.ease_factor,
            cp.repetitions,
            CASE 
                WHEN cp.next_review_date IS NULL THEN 'new'
                WHEN cp.next_review_date <= CURDATE() THEN 'due'
                WHEN cp.interval_days < 7 THEN 'learning'
                ELSE 'mastered'
            END AS status
        FROM cards c
        LEFT JOIN card_performance cp ON c.card_id = cp.card_id AND cp.user_id = %s
        WHERE c.deck_id = %s
        ORDER BY c.created_at DESC
    """, (user_id, deck_id))
    
    cards = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return cards


def create_card(deck_id, user_id, front_content, back_content):
    """Create a new card in a deck"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Verify deck ownership
    cursor.execute("SELECT user_id FROM decks WHERE deck_id = %s", (deck_id,))
    deck = cursor.fetchone()
    
    if not deck or deck['user_id'] != user_id:
        cursor.close()
        conn.close()
        return None
    
    cursor.execute(
        "INSERT INTO cards (deck_id, front_content, back_content) VALUES (%s, %s, %s)",
        (deck_id, front_content, back_content)
    )
    card_id = cursor.lastrowid
    
    # Update statistics
    cursor.execute("""
        INSERT INTO user_statistics (user_id, total_cards)
        VALUES (%s, 1)
        ON DUPLICATE KEY UPDATE total_cards = total_cards + 1
    """, (user_id,))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    # Check for card achievements
    check_card_achievements(user_id)
    
    return card_id


def update_card(card_id, user_id, front_content, back_content):
    """Update a card (owner only)"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Verify ownership
    cursor.execute("""
        SELECT d.user_id 
        FROM cards c 
        JOIN decks d ON c.deck_id = d.deck_id 
        WHERE c.card_id = %s
    """, (card_id,))
    
    card = cursor.fetchone()
    
    if not card or card['user_id'] != user_id:
        cursor.close()
        conn.close()
        return False
    
    cursor.execute(
        "UPDATE cards SET front_content = %s, back_content = %s WHERE card_id = %s",
        (front_content, back_content, card_id)
    )
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return True


def delete_card(card_id, user_id):
    """Delete a card (owner only)"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Verify ownership
    cursor.execute("""
        SELECT d.user_id 
        FROM cards c 
        JOIN decks d ON c.deck_id = d.deck_id 
        WHERE c.card_id = %s
    """, (card_id,))
    
    card = cursor.fetchone()
    
    if not card or card['user_id'] != user_id:
        cursor.close()
        conn.close()
        return False
    
    cursor.execute("DELETE FROM cards WHERE card_id = %s", (card_id,))
    
    # Update statistics
    cursor.execute("""
        UPDATE user_statistics 
        SET total_cards = GREATEST(0, total_cards - 1)
        WHERE user_id = %s
    """, (user_id,))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return True


def bulk_create_cards(deck_id, user_id, cards_data):
    """Bulk create cards from CSV data"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Verify deck ownership
    cursor.execute("SELECT user_id FROM decks WHERE deck_id = %s", (deck_id,))
    deck = cursor.fetchone()
    
    if not deck or deck['user_id'] != user_id:
        cursor.close()
        conn.close()
        return {'inserted': 0, 'failed': len(cards_data), 'errors': ['Unauthorized']}
    
    inserted = 0
    failed = 0
    errors = []
    
    for idx, card in enumerate(cards_data):
        front = card.get('front_content') or card.get('Question') or card.get('question', '')
        back = card.get('back_content') or card.get('Answer') or card.get('answer', '')
        
        if not front or not back:
            failed += 1
            errors.append({'index': idx + 1, 'reason': 'Missing question or answer'})
            continue
        
        try:
            cursor.execute(
                "INSERT INTO cards (deck_id, front_content, back_content) VALUES (%s, %s, %s)",
                (deck_id, str(front).strip(), str(back).strip())
            )
            inserted += 1
        except Exception as e:
            failed += 1
            errors.append({'index': idx + 1, 'reason': str(e)})
    
    # Update statistics
    if inserted > 0:
        cursor.execute("""
            INSERT INTO user_statistics (user_id, total_cards)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE total_cards = total_cards + %s
        """, (user_id, inserted, inserted))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    if inserted > 0:
        check_card_achievements(user_id)
    
    return {'inserted': inserted, 'failed': failed, 'errors': errors[:10]}


# ============================================================================
# STUDY SESSION
# ============================================================================

def get_study_cards(user_id, deck_id=None, limit=20):
    """Get cards due for review"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    if deck_id:
        # Verify deck ownership
        cursor.execute("SELECT user_id FROM decks WHERE deck_id = %s", (deck_id,))
        deck = cursor.fetchone()
        
        if not deck or deck['user_id'] != user_id:
            cursor.close()
            conn.close()
            return []
        
        query = """
            SELECT 
                c.card_id,
                c.deck_id,
                c.front_content,
                c.back_content,
                d.deck_name,
                cp.next_review_date,
                cp.interval_days,
                cp.ease_factor,
                cp.repetitions
            FROM cards c
            JOIN decks d ON c.deck_id = d.deck_id
            LEFT JOIN card_performance cp ON c.card_id = cp.card_id AND cp.user_id = %s
            WHERE d.deck_id = %s AND d.user_id = %s
            AND (cp.next_review_date IS NULL OR cp.next_review_date <= CURDATE())
            ORDER BY cp.next_review_date ASC, c.created_at ASC
            LIMIT %s
        """
        cursor.execute(query, (user_id, deck_id, user_id, limit))
    else:
        # Get from all decks
        query = """
            SELECT 
                c.card_id,
                c.deck_id,
                c.front_content,
                c.back_content,
                d.deck_name,
                cp.next_review_date,
                cp.interval_days,
                cp.ease_factor,
                cp.repetitions
            FROM cards c
            JOIN decks d ON c.deck_id = d.deck_id
            LEFT JOIN card_performance cp ON c.card_id = cp.card_id AND cp.user_id = %s
            WHERE d.user_id = %s
            AND (cp.next_review_date IS NULL OR cp.next_review_date <= CURDATE())
            ORDER BY cp.next_review_date ASC, c.created_at ASC
            LIMIT %s
        """
        cursor.execute(query, (user_id, user_id, limit))
    
    cards = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return cards


def submit_card_review(user_id, card_id, rating):
    """Submit a card review and update spaced repetition data"""
    if rating not in ['forgot', 'hard', 'good', 'easy']:
        return None
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Verify card ownership
    cursor.execute("""
        SELECT d.user_id 
        FROM cards c 
        JOIN decks d ON c.deck_id = d.deck_id 
        WHERE c.card_id = %s
    """, (card_id,))
    
    card = cursor.fetchone()
    
    if not card or card['user_id'] != user_id:
        cursor.close()
        conn.close()
        return None
    
    # Get current performance data
    cursor.execute("""
        SELECT * FROM card_performance 
        WHERE user_id = %s AND card_id = %s
    """, (user_id, card_id))
    
    performance = cursor.fetchone()
    
    # Calculate new values using SM-2
    if performance:
        current_interval = performance['interval_days']
        current_ease = float(performance['ease_factor'])
        repetitions = performance['repetitions']
    else:
        current_interval = 0
        current_ease = 2.5
        repetitions = 0
    
    new_interval, new_ease, new_repetitions = calculate_sm2(
        rating, current_interval, current_ease, repetitions
    )
    next_review = date.today() + timedelta(days=new_interval)
    
    # Update or insert performance record
    if performance:
        cursor.execute("""
            UPDATE card_performance 
            SET next_review_date = %s, interval_days = %s, ease_factor = %s, 
                repetitions = %s, last_reviewed = NOW()
            WHERE user_id = %s AND card_id = %s
        """, (next_review, new_interval, new_ease, new_repetitions, user_id, card_id))
    else:
        cursor.execute("""
            INSERT INTO card_performance 
            (user_id, card_id, next_review_date, interval_days, ease_factor, repetitions, last_reviewed)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
        """, (user_id, card_id, next_review, new_interval, new_ease, new_repetitions))
    
    # Award points based on rating
    points_map = {'forgot': 5, 'hard': 10, 'good': 15, 'easy': 20}
    points = points_map[rating]
    
    cursor.execute(
        "UPDATE users SET points = points + %s WHERE user_id = %s",
        (points, user_id)
    )
    
    # Log study activity
    today = date.today()
    cursor.execute("""
        INSERT INTO study_log (user_id, study_date, cards_reviewed, flashcards_reviewed, points_earned)
        VALUES (%s, %s, 1, 1, %s)
        ON DUPLICATE KEY UPDATE 
            cards_reviewed = cards_reviewed + 1,
            flashcards_reviewed = flashcards_reviewed + 1,
            points_earned = points_earned + %s
    """, (user_id, today, points, points))
    
    # Update user statistics
    cursor.execute("""
        INSERT INTO user_statistics (user_id, flashcards_reviewed, total_points)
        VALUES (%s, 1, %s)
        ON DUPLICATE KEY UPDATE 
            flashcards_reviewed = flashcards_reviewed + 1,
            total_points = total_points + %s
    """, (user_id, points, points))
    
    # Check if card is now mastered (interval >= 21 days)
    if new_interval >= 21:
        cursor.execute("""
            UPDATE user_statistics 
            SET cards_mastered = cards_mastered + 1
            WHERE user_id = %s
        """, (user_id,))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    # Check achievements
    check_study_achievements(user_id)
    
    return {
        'next_review_date': next_review.isoformat(),
        'interval': new_interval,
        'points_earned': points
    }


# ============================================================================
# STATISTICS
# ============================================================================

def get_user_stats(user_id):
    """Get comprehensive user statistics"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Total decks
    cursor.execute("SELECT COUNT(*) AS total FROM decks WHERE user_id = %s", (user_id,))
    total_decks = cursor.fetchone()['total']
    
    # Total cards
    cursor.execute("""
        SELECT COUNT(*) AS total 
        FROM cards c 
        JOIN decks d ON c.deck_id = d.deck_id 
        WHERE d.user_id = %s
    """, (user_id,))
    total_cards = cursor.fetchone()['total']
    
    # Cards due today
    cursor.execute("""
        SELECT COUNT(*) AS total 
        FROM card_performance cp 
        WHERE cp.user_id = %s AND cp.next_review_date <= CURDATE()
    """, (user_id,))
    cards_due = cursor.fetchone()['total']
    
    # New cards (never reviewed)
    cursor.execute("""
        SELECT COUNT(*) AS total 
        FROM cards c 
        JOIN decks d ON c.deck_id = d.deck_id 
        LEFT JOIN card_performance cp ON c.card_id = cp.card_id AND cp.user_id = %s
        WHERE d.user_id = %s AND cp.card_id IS NULL
    """, (user_id, user_id))
    new_cards = cursor.fetchone()['total']
    
    # Upcoming reviews (next 7 days)
    cursor.execute("""
        SELECT COUNT(*) AS total 
        FROM card_performance cp 
        WHERE cp.user_id = %s 
        AND cp.next_review_date > CURDATE() 
        AND cp.next_review_date <= DATE_ADD(CURDATE(), INTERVAL 7 DAY)
    """, (user_id,))
    cards_upcoming = cursor.fetchone()['total']
    
    # Total points
    cursor.execute("SELECT points FROM users WHERE user_id = %s", (user_id,))
    total_points = cursor.fetchone()['points']
    
    # Current streak
    cursor.execute("""
        SELECT study_date FROM study_log 
        WHERE user_id = %s ORDER BY study_date DESC
    """, (user_id,))
    study_dates = [row['study_date'] for row in cursor.fetchall()]
    current_streak = calculate_streak(study_dates)
    
    # Cards reviewed today
    today = date.today()
    cursor.execute("""
        SELECT COALESCE(flashcards_reviewed, 0) AS reviewed
        FROM study_log 
        WHERE user_id = %s AND study_date = %s
    """, (user_id, today))
    result = cursor.fetchone()
    cards_reviewed_today = result['reviewed'] if result else 0
    
    cursor.close()
    conn.close()
    
    return {
        'total_decks': total_decks,
        'total_cards': total_cards,
        'cards_due': cards_due + new_cards,  # Include new cards
        'new_cards': new_cards,
        'cards_upcoming': cards_upcoming,
        'total_points': total_points,
        'current_streak': current_streak,
        'cards_reviewed_today': cards_reviewed_today
    }


def calculate_streak(study_dates):
    """Calculate current study streak from list of study dates"""
    if not study_dates:
        return 0
    
    today = date.today()
    streak = 0
    
    # Check if studied today or yesterday to start counting
    first_date = study_dates[0]
    if first_date == today or first_date == today - timedelta(days=1):
        expected_date = first_date
        
        for study_date in study_dates:
            if study_date == expected_date:
                streak += 1
                expected_date -= timedelta(days=1)
            else:
                break
    
    return streak


def get_study_log(user_id, limit=30):
    """Get recent study activity"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT study_date, cards_reviewed, flashcards_reviewed, mcqs_reviewed, points_earned
        FROM study_log
        WHERE user_id = %s
        ORDER BY study_date DESC
        LIMIT %s
    """, (user_id, limit))
    
    logs = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return logs


# ============================================================================
# ACHIEVEMENTS
# ============================================================================

def check_deck_achievements(user_id):
    """Check and award deck-related achievements"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT COUNT(*) AS count FROM decks WHERE user_id = %s", (user_id,))
    deck_count = cursor.fetchone()['count']
    
    achievements_to_check = []
    if deck_count >= 1:
        achievements_to_check.append('first_deck')
    if deck_count >= 5:
        achievements_to_check.append('deck_collector')
    
    for code in achievements_to_check:
        award_achievement(cursor, conn, user_id, code)
    
    conn.commit()
    cursor.close()
    conn.close()


def check_card_achievements(user_id):
    """Check and award card-related achievements"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT COUNT(*) AS count 
        FROM cards c 
        JOIN decks d ON c.deck_id = d.deck_id 
        WHERE d.user_id = %s
    """, (user_id,))
    card_count = cursor.fetchone()['count']
    
    achievements_to_check = []
    if card_count >= 50:
        achievements_to_check.append('card_creator')
    if card_count >= 250:
        achievements_to_check.append('knowledge_builder')
    
    for code in achievements_to_check:
        award_achievement(cursor, conn, user_id, code)
    
    conn.commit()
    cursor.close()
    conn.close()


def check_study_achievements(user_id):
    """Check and award study-related achievements"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Check for first study session
    cursor.execute("SELECT COUNT(*) AS count FROM study_log WHERE user_id = %s", (user_id,))
    if cursor.fetchone()['count'] > 0:
        award_achievement(cursor, conn, user_id, 'first_study')
    
    # Check streak achievements
    cursor.execute("""
        SELECT study_date FROM study_log 
        WHERE user_id = %s ORDER BY study_date DESC
    """, (user_id,))
    study_dates = [row['study_date'] for row in cursor.fetchall()]
    streak = calculate_streak(study_dates)
    
    if streak >= 7:
        award_achievement(cursor, conn, user_id, 'study_streak_7')
    if streak >= 30:
        award_achievement(cursor, conn, user_id, 'study_streak_30')
    
    # Check point achievements
    cursor.execute("SELECT points FROM users WHERE user_id = %s", (user_id,))
    points = cursor.fetchone()['points']
    
    if points >= 100:
        award_achievement(cursor, conn, user_id, 'point_collector_100')
    if points >= 1000:
        award_achievement(cursor, conn, user_id, 'point_master_1000')
    
    # Check mastered cards
    cursor.execute("""
        SELECT cards_mastered FROM user_statistics WHERE user_id = %s
    """, (user_id,))
    result = cursor.fetchone()
    if result and result['cards_mastered'] >= 10:
        award_achievement(cursor, conn, user_id, 'mastered_cards_10')
    
    conn.commit()
    cursor.close()
    conn.close()


def award_achievement(cursor, conn, user_id, achievement_code):
    """Award an achievement if not already earned"""
    try:
        cursor.execute(
            "SELECT achievement_id FROM achievements WHERE achievement_code = %s",
            (achievement_code,)
        )
        achievement = cursor.fetchone()
        
        if not achievement:
            return False
        
        # Check if already earned
        cursor.execute("""
            SELECT id FROM user_achievements 
            WHERE user_id = %s AND achievement_id = %s
        """, (user_id, achievement['achievement_id']))
        
        if cursor.fetchone():
            return False
        
        # Award achievement
        cursor.execute("""
            INSERT INTO user_achievements (user_id, achievement_id)
            VALUES (%s, %s)
        """, (user_id, achievement['achievement_id']))
        
        # Bonus points
        cursor.execute(
            "UPDATE users SET points = points + 100 WHERE user_id = %s",
            (user_id,)
        )
        
        return True
    except Exception as e:
        print(f"Error awarding achievement {achievement_code}: {e}")
        return False
