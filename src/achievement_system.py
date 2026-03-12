"""
Achievement System - Refactored with Category-Based Classes
This module provides a cleaner, more maintainable achievement checking system
"""

from datetime import datetime, timedelta


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
            self.cursor.execute("""
                INSERT INTO user_achievements (user_id, achievement_id, progress_when_unlocked)
                VALUES (%s, %s, %s)
            """, (self.user_id, achievement['achievement_id'], progress_value))
            self.newly_unlocked.append(achievement)
            print(f"🏆 Unlocked: {achievement['icon']} {achievement['title']}")
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
    
    SUBJECT_CODES = {
        'Physics': 'physics_starter',
        'Chemistry': 'chemistry_starter',
        'Biology': 'biology_starter',
        'Mathematics': 'mathematics_starter'
    }
    
    def check(self, stats, subject):
        """Check all subject-related achievements"""
        subject_lower = subject.lower()
        
        # First quiz overall
        if stats['total_quizzes_completed'] == 1:
            self.check_achievement('first_steps')
        
        # First quiz per subject
        if subject in self.SUBJECT_CODES and stats[f'{subject_lower}_quizzes'] == 1:
            self.check_achievement(self.SUBJECT_CODES[subject])
        
        # All-rounder: completed all 4 subjects
        if (stats['physics_completed'] and stats['chemistry_completed'] and 
            stats['biology_completed'] and stats['mathematics_completed']):
            self.check_achievement('all_rounder')
        
        # Subject lover: 10 quizzes in one subject
        for subj in ['physics', 'chemistry', 'biology', 'mathematics']:
            if stats[f'{subj}_quizzes'] >= 10:
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
        if (stats['physics_perfect_count'] > 0 and stats['chemistry_perfect_count'] > 0 and
            stats['biology_perfect_count'] > 0 and stats['mathematics_perfect_count'] > 0):
            self.check_achievement('perfectionist')
        
        # Precision Player: 5 consecutive 90%+ quizzes
        if recent_90_plus >= 5:
            self.check_achievement('precision_player')
        
        return self.newly_unlocked


class AccuracyAchievements(AchievementChecker):
    """Checks accuracy-based achievements"""
    
    def check(self, max_consecutive):
        """Check all accuracy achievements"""
        
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
        # Initialize user statistics if not exists
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
        
        # Get previous statistics
        cur.execute("SELECT * FROM user_statistics WHERE user_id = %s", (user_id,))
        old_stats = cur.fetchone()
        
        # Calculate streak
        last_quiz_date = old_stats['last_quiz_date'] if old_stats and old_stats['last_quiz_date'] else None
        current_streak = old_stats['current_streak_days'] if old_stats else 0
        
        today = datetime.now().date()
        if last_quiz_date:
            days_diff = (today - last_quiz_date).days
            if days_diff == 0:
                # Same day, keep streak
                pass
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
        
        # Count high scores (90%+) for precision player
        cur.execute("""
            SELECT COUNT(*) as count FROM (
                SELECT percentage FROM results 
                WHERE user_id = %s AND percentage >= 90
                ORDER BY result_id DESC LIMIT 5
            ) recent
        """, (user_id,))
        recent_90_plus = cur.fetchone()['count']
        
        # Update user statistics
        subject_lower = subject.lower()
        cur.execute(f"""
            UPDATE user_statistics 
            SET 
                total_quizzes_completed = total_quizzes_completed + 1,
                total_questions_solved = total_questions_solved + %s,
                total_correct_answers = total_correct_answers + %s,
                {subject_lower}_quizzes = {subject_lower}_quizzes + 1,
                perfect_quizzes_count = perfect_quizzes_count + %s,
                {subject_lower}_perfect_count = {subject_lower}_perfect_count + %s,
                {subject_lower}_completed = TRUE,
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
            1 if percentage == 100 else 0,
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
        
    except Exception as e:
        print(f"Error checking achievements: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return []
    finally:
        cur.close()
