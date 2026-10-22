"""
Achievement System - Refactored with Category-Based Classes
This module provides a cleaner, more maintainable achievement checking system
"""

import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# The only subjects that have dedicated per-subject columns in user_statistics
# (`<subject>_quizzes`, `<subject>_perfect_count`, `<subject>_completed`).
#
# This mapping is the whitelist that keeps `subject` out of raw SQL. Quizzes can
# also be started from the MCQ category browser, where the "subject" is really a
# category name ('Computer Science', 'History', 'General Knowledge', ...). Those
# have no per-subject columns, so they update the global counters only - they
# must never be interpolated into a statement.
VALID_SUBJECTS = {
    'physics': 'physics',
    'chemistry': 'chemistry',
    'biology': 'biology',
    'mathematics': 'mathematics',
}


def resolve_subject_column_prefix(subject):
    """
    Map a free-form subject/category name to a safe column prefix.

    Returns None when the subject has no per-subject columns, which is the
    signal to skip the subject-specific part of the statistics update rather
    than build an invalid (or injectable) statement.
    """
    if not subject:
        return None
    return VALID_SUBJECTS.get(str(subject).strip().lower())


class AchievementChecker:
    """Base class for achievement checking logic"""
    
    def __init__(self, conn, user_id, cursor):
        self.conn = conn
        self.user_id = user_id
        self.cursor = cursor
        self.newly_unlocked = []
    
    def check_achievement(self, achievement_code, progress_value=100):
        """Helper to check and unlock a specific achievement"""
        self.cursor.execute("""
            SELECT a.achievement_id, a.title, a.icon, a.description
            FROM achievements a
            WHERE a.achievement_code = %s
            AND NOT EXISTS (
                SELECT 1 FROM user_achievements ua 
                WHERE ua.user_id = %s AND ua.achievement_id = a.achievement_id
            )
        """, (achievement_code, self.user_id))
        
        achievement = self.cursor.fetchone()
        if achievement:
            try:
                self.cursor.execute("""
                    INSERT INTO user_achievements (user_id, achievement_id, progress_when_unlocked)
                    VALUES (%s, %s, %s)
                """, (self.user_id, achievement['achievement_id'], progress_value))
            except Exception as e:
                # Two concurrent submissions can both pass the NOT EXISTS check
                # above before either commits. Swallow only that duplicate-key
                # race (MySQL 1062) - letting it escape would roll back the
                # caller's whole transaction, discarding unrelated stats
                # updates for a harmless collision.
                if getattr(e, 'errno', None) == 1062:
                    logger.debug(
                        'Achievement %s already unlocked for user %s (concurrent insert)',
                        achievement_code, self.user_id
                    )
                    return False
                raise
            self.newly_unlocked.append(achievement)
            logger.info(
                'Unlocked achievement %s for user %s', achievement_code, self.user_id
            )
            return True
        return False


class MilestoneAchievements(AchievementChecker):
    """Checks milestone-based achievements (total quizzes, questions)"""
    
    def check(self, stats):
        """Check all milestone achievements"""
        total_quizzes = stats['total_quizzes_completed']
        total_questions = stats['total_questions_solved']
        
        if total_quizzes >= 1:
            self.check_achievement('quiz_rookie')
        if total_quizzes >= 10:
            self.check_achievement('quiz_enthusiast')
        if total_quizzes >= 50:
            self.check_achievement('quiz_pro')
        if total_quizzes >= 100:
            self.check_achievement('quiz_legend')
        if total_questions >= 200:
            self.check_achievement('knowledge_seeker')
        
        return self.newly_unlocked


class SubjectAchievements(AchievementChecker):
    """Checks subject-specific achievements"""
    
    # Keyed by the lowercase column prefix so lookups are case-insensitive
    # ('/quiz/physics' and '/quiz/Physics' must behave identically).
    SUBJECT_CODES = {
        'physics': 'physics_starter',
        'chemistry': 'chemistry_starter',
        'biology': 'biology_starter',
        'mathematics': 'mathematics_starter'
    }

    def check(self, stats, subject):
        """Check all subject-related achievements"""
        # None for MCQ category names that have no per-subject columns.
        column_prefix = resolve_subject_column_prefix(subject)

        # First quiz overall
        if stats['total_quizzes_completed'] == 1:
            self.check_achievement('first_steps')

        # First quiz per subject
        if column_prefix and stats.get(f'{column_prefix}_quizzes') == 1:
            self.check_achievement(self.SUBJECT_CODES[column_prefix])

        # All-rounder: completed all 4 subjects
        if all(stats.get(f'{subj}_completed') for subj in VALID_SUBJECTS):
            self.check_achievement('all_rounder')

        # Subject lover: 10 quizzes in one subject
        for subj in VALID_SUBJECTS:
            if (stats.get(f'{subj}_quizzes') or 0) >= 10:
                self.check_achievement('subject_lover')
                break

        return self.newly_unlocked


class PerfectScoreAchievements(AchievementChecker):
    """Checks perfect score and precision-based achievements"""
    
    def check(self, stats, percentage, recent_90_plus):
        """Check all perfect score achievements"""
        
        # Flawless Victory: 100% score
        if percentage == 100:
            self.check_achievement('flawless_victory')
        
        # Perfectionist: 100% in all subjects
        if all((stats.get(f'{subj}_perfect_count') or 0) > 0 for subj in VALID_SUBJECTS):
            self.check_achievement('perfectionist')

        # Precision Player: all of the 5 most recent quizzes scored 90%+
        if recent_90_plus >= 5:
            self.check_achievement('precision_player')
        
        return self.newly_unlocked


class AccuracyAchievements(AchievementChecker):
    """Checks accuracy-based achievements"""
    
    def check(self, max_consecutive):
        """
        Check all accuracy achievements.

        Note: `max_consecutive` is tracked at quiz granularity, not per answer -
        only a fully perfect quiz adds to the run, and any quiz with a wrong
        answer resets it. So 'sharp_shooter' means "perfect quizzes totalling 10+
        answers in a row", not a true answer-by-answer streak. Answer-level
        tracking would need per-answer bookkeeping across quizzes; the
        achievement description reflects the quiz-level behaviour instead.
        """
        if max_consecutive >= 10:
            self.check_achievement('sharp_shooter')

        return self.newly_unlocked


class TimeBasedAchievements(AchievementChecker):
    """Checks time-based achievements (speed, time of day)"""
    
    def check(self, avg_time_per_question, time_of_day):
        """Check all time-based achievements"""
        
        if avg_time_per_question <= 60:
            self.check_achievement('fast_thinker')
        
        if time_of_day == 'night_owl':
            self.check_achievement('night_owl')
        
        if time_of_day == 'early_bird':
            self.check_achievement('early_bird')
        
        return self.newly_unlocked


class StreakAchievements(AchievementChecker):
    """Checks daily streak achievements"""
    
    def check(self, current_streak):
        """Check all streak achievements"""
        
        if current_streak >= 3:
            self.check_achievement('steady_learner')
        if current_streak >= 7:
            self.check_achievement('consistency_streak')
        
        return self.newly_unlocked


class ImprovementAchievements(AchievementChecker):
    """Checks improvement-based achievements"""
    
    def check(self, percentage, subject, result_id):
        """Check improvement achievements"""
        
        # Comeback Kid: 20% improvement from previous attempt
        self.cursor.execute("""
            SELECT percentage FROM results 
            WHERE user_id = %s AND subject = %s AND result_id < %s
            ORDER BY result_id DESC LIMIT 1
        """, (self.user_id, subject, result_id))
        
        prev_result = self.cursor.fetchone()
        if prev_result:
            improvement = percentage - float(prev_result['percentage'])
            if improvement >= 20:
                self.check_achievement('comeback_kid', int(improvement))
        
        return self.newly_unlocked


class SessionAchievements(AchievementChecker):
    """Checks session-based achievements (marathon, etc.)"""
    
    def check(self):
        """Check session-based achievements"""
        
        # Marathon: 5 quizzes in last hour
        one_hour_ago = datetime.now() - timedelta(hours=1)
        self.cursor.execute("""
            SELECT COUNT(*) as count FROM quiz_sessions
            WHERE user_id = %s AND end_time >= %s
        """, (self.user_id, one_hour_ago))
        
        recent_quizzes = self.cursor.fetchone()['count']
        if recent_quizzes >= 5:
            self.check_achievement('marathon_session')
        
        return self.newly_unlocked


class RetryAchievements(AchievementChecker):
    """Checks retry-based achievements (Retry Champion)"""
    
    def check(self, subject, percentage):
        """Check retry achievements"""
        import json
        
        # Get current quiz_retakes data
        self.cursor.execute("""
            SELECT quiz_retakes FROM user_statistics WHERE user_id = %s
        """, (self.user_id,))
        
        result = self.cursor.fetchone()
        quiz_retakes = result['quiz_retakes'] if result and result['quiz_retakes'] else {}
        
        # Parse JSON if it's a string
        if isinstance(quiz_retakes, str):
            quiz_retakes = json.loads(quiz_retakes)
        
        # Initialize subject if not exists
        if subject not in quiz_retakes:
            quiz_retakes[subject] = []
        
        # Add current score
        quiz_retakes[subject].append(int(percentage))
        
        # Check for Retry Champion: 5+ attempts with consistent improvement
        if len(quiz_retakes[subject]) >= 5:
            scores = quiz_retakes[subject][-5:]  # Last 5 scores
            improvements = sum(1 for i in range(1, len(scores)) if scores[i] > scores[i-1])
            
            # If at least 3 out of 4 attempts showed improvement
            if improvements >= 3:
                self.check_achievement('retry_champion', len(quiz_retakes[subject]))
        
        # Update quiz_retakes in database
        self.cursor.execute("""
            UPDATE user_statistics 
            SET quiz_retakes = %s
            WHERE user_id = %s
        """, (json.dumps(quiz_retakes), self.user_id))
        
        return self.newly_unlocked


def check_and_unlock_achievements(conn, user_id, subject, score, total, percentage, result_id, quiz_start_time, quiz_end_time):
    """
    Refactored achievement checking system
    Uses category-based classes for better organization and maintainability
    """
    cur = conn.cursor(dictionary=True)
    all_unlocked = []
    
    try:
        # Read any existing statistics row *before* creating one. Creating it
        # first would stamp last_quiz_date = CURDATE(), so a brand-new user's
        # streak calculation below would take the "same day, keep streak"
        # branch and leave the streak at 0 instead of 1 - permanently
        # offsetting every subsequent day for that user.
        cur.execute("SELECT * FROM user_statistics WHERE user_id = %s", (user_id,))
        old_stats = cur.fetchone()
        is_new_user = old_stats is None

        # Initialize user statistics if not exists
        if is_new_user:
            cur.execute("""
                INSERT IGNORE INTO user_statistics (user_id, last_quiz_date)
                VALUES (%s, CURDATE())
            """, (user_id,))

        # Calculate quiz metrics
        duration_seconds = (quiz_end_time - quiz_start_time).total_seconds()
        avg_time_per_question = duration_seconds / total if total > 0 else 0
        hour = quiz_end_time.hour
        
        # Determine time of day
        if 0 <= hour < 5:
            time_of_day = 'night_owl'
        elif 5 <= hour < 8:
            time_of_day = 'early_bird'
        elif 8 <= hour < 12:
            time_of_day = 'morning'
        elif 12 <= hour < 17:
            time_of_day = 'afternoon'
        else:
            time_of_day = 'evening'
        
        # Save quiz session data
        cur.execute("""
            INSERT INTO quiz_sessions 
            (user_id, result_id, subject, start_time, end_time, duration_seconds, 
             avg_time_per_question, time_of_day, quiz_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURDATE())
        """, (user_id, result_id, subject, quiz_start_time, quiz_end_time, 
              duration_seconds, avg_time_per_question, time_of_day))
        
        # Calculate streak (old_stats was read above, before the row was created)
        last_quiz_date = old_stats['last_quiz_date'] if old_stats and old_stats['last_quiz_date'] else None
        current_streak = old_stats['current_streak_days'] if old_stats else 0

        today = datetime.now().date()
        if is_new_user:
            # First ever quiz: day one of the streak.
            current_streak = 1
        elif last_quiz_date:
            days_diff = (today - last_quiz_date).days
            if days_diff == 0:
                # Same day, keep streak (but a pre-existing row that never
                # recorded a quiz still needs to start at 1).
                current_streak = max(current_streak, 1)
            elif days_diff == 1:
                # Consecutive day
                current_streak += 1
            else:
                # Streak broken
                current_streak = 1
        else:
            current_streak = 1
        
        # Update consecutive correct answers
        consecutive_correct = old_stats['consecutive_correct_answers'] if old_stats else 0
        if score == total:  # All correct
            consecutive_correct += score
        else:
            consecutive_correct = 0
        
        max_consecutive = max(consecutive_correct, old_stats['max_consecutive_correct'] if old_stats else 0)
        
        # Update consecutive perfect quizzes
        consecutive_perfect = old_stats['consecutive_perfect_quizzes'] if old_stats else 0
        if percentage == 100:
            consecutive_perfect += 1
        elif percentage < 90:  # Reset only if below 90%
            consecutive_perfect = 0
        
        # Count how many of the 5 MOST RECENT quizzes scored 90%+.
        # The >= 90 filter must stay in the outer query: filtering inside the
        # subquery would pick the 5 most recent *90%+* results regardless of
        # what happened in between, turning "5 consecutive" into "5 ever".
        cur.execute("""
            SELECT COUNT(*) as count FROM (
                SELECT percentage FROM results
                WHERE user_id = %s
                ORDER BY result_id DESC LIMIT 5
            ) recent
            WHERE recent.percentage >= 90
        """, (user_id,))
        recent_90_plus = cur.fetchone()['count']
        
        # Update user statistics.
        #
        # `subject` reaches us from request JSON / the session, and quizzes
        # started from the MCQ category browser carry a category name rather
        # than one of the four real subjects. Resolve it through the whitelist
        # and only then build the per-subject assignments: anything unknown
        # (e.g. 'Computer Science') updates the global counters only.
        # Interpolating it directly would be a SQL injection, and would also
        # break outright on names with spaces or without matching columns.
        column_prefix = resolve_subject_column_prefix(subject)

        subject_assignments = ''
        subject_params = []
        if column_prefix:
            subject_assignments = f"""
                {column_prefix}_quizzes = {column_prefix}_quizzes + 1,
                {column_prefix}_perfect_count = {column_prefix}_perfect_count + %s,
                {column_prefix}_completed = TRUE,"""
            subject_params = [1 if percentage == 100 else 0]
        else:
            logger.info(
                "Subject %r has no per-subject statistics columns; "
                "recording global statistics only.", subject
            )

        cur.execute(f"""
            UPDATE user_statistics
            SET
                total_quizzes_completed = total_quizzes_completed + 1,
                total_questions_solved = total_questions_solved + %s,
                total_correct_answers = total_correct_answers + %s,
                perfect_quizzes_count = perfect_quizzes_count + %s,{subject_assignments}
                current_streak_days = %s,
                longest_streak_days = GREATEST(longest_streak_days, %s),
                last_quiz_date = CURDATE(),
                consecutive_perfect_quizzes = %s,
                consecutive_correct_answers = %s,
                max_consecutive_correct = %s,
                night_owl_count = night_owl_count + %s,
                early_bird_count = early_bird_count + %s
            WHERE user_id = %s
        """, (
            total, score,
            1 if percentage == 100 else 0,
            *subject_params,
            current_streak, current_streak,
            consecutive_perfect,
            consecutive_correct, max_consecutive,
            1 if time_of_day == 'night_owl' else 0,
            1 if time_of_day == 'early_bird' else 0,
            user_id
        ))
        
        # Get updated statistics
        cur.execute("SELECT * FROM user_statistics WHERE user_id = %s", (user_id,))
        stats = cur.fetchone()
        
        # ===== CHECK ALL ACHIEVEMENT CATEGORIES =====
        
        # 1. Milestone Achievements
        milestone_checker = MilestoneAchievements(conn, user_id, cur)
        all_unlocked.extend(milestone_checker.check(stats))
        
        # 2. Subject Achievements
        subject_checker = SubjectAchievements(conn, user_id, cur)
        all_unlocked.extend(subject_checker.check(stats, subject))
        
        # 3. Perfect Score Achievements
        perfect_checker = PerfectScoreAchievements(conn, user_id, cur)
        all_unlocked.extend(perfect_checker.check(stats, percentage, recent_90_plus))
        
        # 4. Accuracy Achievements
        accuracy_checker = AccuracyAchievements(conn, user_id, cur)
        all_unlocked.extend(accuracy_checker.check(max_consecutive))
        
        # 5. Time-Based Achievements
        time_checker = TimeBasedAchievements(conn, user_id, cur)
        all_unlocked.extend(time_checker.check(avg_time_per_question, time_of_day))
        
        # 6. Streak Achievements
        streak_checker = StreakAchievements(conn, user_id, cur)
        all_unlocked.extend(streak_checker.check(current_streak))
        
        # 7. Improvement Achievements
        improvement_checker = ImprovementAchievements(conn, user_id, cur)
        all_unlocked.extend(improvement_checker.check(percentage, subject, result_id))
        
        # 8. Session Achievements
        session_checker = SessionAchievements(conn, user_id, cur)
        all_unlocked.extend(session_checker.check())
        
        # 9. Retry Achievements (NEW)
        retry_checker = RetryAchievements(conn, user_id, cur)
        all_unlocked.extend(retry_checker.check(subject, percentage))
        
        conn.commit()
        return all_unlocked
        
    except Exception:
        logger.error(
            'Error checking achievements for user %s (subject=%r)',
            user_id, subject, exc_info=True
        )
        conn.rollback()
        return []
    finally:
        cur.close()
