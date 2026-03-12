"""
Import flashcard CSV files into the database
Creates decks for each subject and imports cards from CSV files
"""

import sys
import os
import csv

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.db_config import get_connection
from src.flashcard_system import create_deck, bulk_create_cards


def get_or_create_admin_user():
    """Get the first admin user or create a system user for flashcards"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Try to find an admin user
    cursor.execute("SELECT user_id FROM users WHERE is_admin = TRUE LIMIT 1")
    admin = cursor.fetchone()
    
    if admin:
        user_id = admin['user_id']
        print(f"Using admin user ID: {user_id}")
    else:
        # Create a system user for flashcards if no admin exists
        print("No admin user found. Creating system user for flashcards...")
        cursor.execute("""
            INSERT INTO users (username, password_hash, email, full_name, is_admin)
            VALUES ('system', 'locked', 'system@flashcards.local', 'System Flashcards', FALSE)
            ON DUPLICATE KEY UPDATE user_id=LAST_INSERT_ID(user_id)
        """)
        conn.commit()
        user_id = cursor.lastrowid
        if user_id == 0:
            cursor.execute("SELECT user_id FROM users WHERE username = 'system'")
            user_id = cursor.fetchone()['user_id']
        print(f"Created system user with ID: {user_id}")
    
    cursor.close()
    conn.close()
    return user_id


def import_flashcard_csv(csv_file, deck_name, deck_description, user_id):
    """Import flashcards from a CSV file into a new deck"""
    
    # Check if file exists
    if not os.path.exists(csv_file):
        print(f"Error: File not found: {csv_file}")
        return False
    
    print(f"\n{'='*60}")
    print(f"Importing: {deck_name}")
    print(f"File: {csv_file}")
    print(f"{'='*60}")
    
    # Read CSV file
    cards_data = []
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            csv_reader = csv.DictReader(f)
            for row in csv_reader:
                cards_data.append(row)
        
        print(f"Read {len(cards_data)} cards from CSV")
        
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return False
    
    # Check if deck already exists
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute(
        "SELECT deck_id FROM decks WHERE user_id = %s AND deck_name = %s",
        (user_id, deck_name)
    )
    existing_deck = cursor.fetchone()
    
    if existing_deck:
        print(f"Deck '{deck_name}' already exists with ID: {existing_deck['deck_id']}")
        deck_id = existing_deck['deck_id']
        
        # Option to skip or update
        response = input("Do you want to add these cards to the existing deck? (y/n): ")
        if response.lower() != 'y':
            print("Skipping...")
            cursor.close()
            conn.close()
            return True
    else:
        # Create new deck
        deck_id = create_deck(user_id, deck_name, deck_description)
        if not deck_id:
            print(f"Error: Failed to create deck '{deck_name}'")
            cursor.close()
            conn.close()
            return False
        print(f"Created new deck with ID: {deck_id}")
    
    cursor.close()
    conn.close()
    
    # Import cards
    result = bulk_create_cards(deck_id, user_id, cards_data)
    
    print(f"\nImport Results:")
    print(f"  ✓ Successfully imported: {result['inserted']} cards")
    print(f"  ✗ Failed: {result['failed']} cards")
    
    if result['errors']:
        print(f"\nErrors (showing first 5):")
        for error in result['errors'][:5]:
            print(f"  - Card {error.get('index', '?')}: {error.get('reason', 'Unknown error')}")
    
    return True


def main():
    """Main import function"""
    print("\n" + "="*60)
    print("FLASHCARD CSV IMPORT TOOL")
    print("="*60)
    
    # Get user ID
    user_id = get_or_create_admin_user()
    
    # Define CSV files and their corresponding deck information
    base_path = os.path.join(os.path.dirname(__file__), '..', 'data')
    
    flashcard_files = [
        {
            'file': os.path.join(base_path, 'biology_flashcards.csv'),
            'deck_name': 'Biology Flashcards',
            'description': 'Comprehensive biology questions covering cells, organs, systems, and life processes'
        },
        {
            'file': os.path.join(base_path, 'chemistry_flashcards.csv'),
            'deck_name': 'Chemistry Flashcards',
            'description': 'Essential chemistry concepts including elements, compounds, reactions, and acids/bases'
        },
        {
            'file': os.path.join(base_path, 'physics_flashcards.csv'),
            'deck_name': 'Physics Flashcards',
            'description': 'Physics fundamentals covering motion, energy, electricity, light, and forces'
        },
        {
            'file': os.path.join(base_path, 'maths_flashcards.csv'),
            'deck_name': 'Mathematics Flashcards',
            'description': 'Mathematics problems including algebra, geometry, trigonometry, and statistics'
        }
    ]
    
    # Import each file
    success_count = 0
    for flashcard_info in flashcard_files:
        success = import_flashcard_csv(
            flashcard_info['file'],
            flashcard_info['deck_name'],
            flashcard_info['description'],
            user_id
        )
        if success:
            success_count += 1
    
    print(f"\n{'='*60}")
    print(f"IMPORT COMPLETE")
    print(f"Successfully imported {success_count}/{len(flashcard_files)} files")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nImport cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError during import: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
