# Quiz Master Application - Source Package
# Contains core application modules

from .db_config import get_connection
from .achievement_system import check_and_unlock_achievements
from .flashcard_system import (
    get_user_decks, create_deck, get_deck, delete_deck,
    get_deck_cards, create_card, update_card, delete_card, bulk_create_cards,
    get_study_cards, submit_card_review, get_user_stats, get_study_log,
    calculate_sm2, get_review_intervals
)

__all__ = [
    'get_connection',
    'check_and_unlock_achievements',
    'get_user_decks', 'create_deck', 'get_deck', 'delete_deck',
    'get_deck_cards', 'create_card', 'update_card', 'delete_card', 'bulk_create_cards',
    'get_study_cards', 'submit_card_review', 'get_user_stats', 'get_study_log',
    'calculate_sm2', 'get_review_intervals'
]
