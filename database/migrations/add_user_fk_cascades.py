"""
Add ON DELETE CASCADE foreign keys on user_id.

`results` and `user_sessions` already reference users(user_id) with CASCADE,
but user_statistics, user_achievements, marked_questions and quiz_sessions
store user_id as a plain int with no constraint at all. Deleting a user
therefore leaves rows behind that point at a user_id that no longer exists -
they still show up in aggregates such as the leaderboard and achievement
counts, and a later user can be issued the same auto-increment id and inherit
them.

Safe to run more than once: it skips any constraint that already exists, and
clears existing orphans first (the constraint cannot be created while rows
violate it).
"""

import os
import sys

# Make src/ importable so this runs from the repo root, the way the
# README documents it (python database/migrations/add_user_fk_cascades.py).
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'src'))

from db_config import get_db_connection

# Windows consoles default to cp1252, which cannot encode the emoji in this
# script's progress output.
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')


# table -> constraint name to create
TABLES = {
    'user_statistics': 'fk_user_statistics_user',
    'user_achievements': 'fk_user_achievements_user',
    'marked_questions': 'fk_marked_questions_user',
    'quiz_sessions': 'fk_quiz_sessions_user',
}


def existing_user_fk(cur, table):
    """Return the name of an existing user_id -> users FK, or None."""
    cur.execute("""
        SELECT k.CONSTRAINT_NAME
        FROM information_schema.KEY_COLUMN_USAGE k
        WHERE k.TABLE_SCHEMA = DATABASE()
          AND k.TABLE_NAME = %s
          AND k.COLUMN_NAME = 'user_id'
          AND k.REFERENCED_TABLE_NAME = 'users'
        LIMIT 1
    """, (table,))
    row = cur.fetchone()
    return row[0] if row else None


def main():
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            print('=' * 60)
            print('ADDING ON DELETE CASCADE FOREIGN KEYS')
            print('=' * 60)

            for table, constraint in TABLES.items():
                print(f'\n{table}:')

                existing = existing_user_fk(cur, table)
                if existing:
                    print(f'   already constrained by {existing} - skipping')
                    continue

                # The constraint cannot be added while violating rows exist.
                cur.execute(f"""
                    DELETE FROM `{table}`
                    WHERE user_id IS NOT NULL
                      AND user_id NOT IN (SELECT user_id FROM users)
                """)
                removed = cur.rowcount
                if removed:
                    print(f'   removed {removed} orphaned row(s)')
                else:
                    print('   no orphaned rows')

                # An index on user_id is required to support the constraint.
                cur.execute("""
                    SELECT COUNT(*) FROM information_schema.STATISTICS
                    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s
                      AND COLUMN_NAME = 'user_id' AND SEQ_IN_INDEX = 1
                """, (table,))
                if cur.fetchone()[0] == 0:
                    cur.execute(f'CREATE INDEX `idx_{table}_user_id` ON `{table}` (user_id)')
                    print('   created supporting index on user_id')

                cur.execute(f"""
                    ALTER TABLE `{table}`
                    ADD CONSTRAINT `{constraint}`
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                    ON DELETE CASCADE
                """)
                print(f'   ✅ added {constraint} ON DELETE CASCADE')

            conn.commit()

            print('\n' + '=' * 60)
            print('VERIFICATION')
            print('=' * 60)
            for table in list(TABLES) + ['results', 'user_sessions']:
                cur.execute("""
                    SELECT k.CONSTRAINT_NAME, r.DELETE_RULE
                    FROM information_schema.KEY_COLUMN_USAGE k
                    JOIN information_schema.REFERENTIAL_CONSTRAINTS r
                      ON r.CONSTRAINT_SCHEMA = k.TABLE_SCHEMA
                     AND r.CONSTRAINT_NAME = k.CONSTRAINT_NAME
                    WHERE k.TABLE_SCHEMA = DATABASE() AND k.TABLE_NAME = %s
                      AND k.COLUMN_NAME = 'user_id'
                      AND k.REFERENCED_TABLE_NAME = 'users'
                """, (table,))
                row = cur.fetchone()
                status = f'{row[0]} -> {row[1]}' if row else 'NO FOREIGN KEY'
                print(f'   {table:20} {status}')

            print('\n✅ MIGRATION COMPLETED SUCCESSFULLY!')

        except Exception as e:
            conn.rollback()
            print(f'\n❌ Migration failed: {e}')
            raise
        finally:
            cur.close()


if __name__ == '__main__':
    main()
