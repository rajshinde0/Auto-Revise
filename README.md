# Quiz Master - MCQ & Flashcard Learning Platform

A comprehensive learning platform built with Flask featuring MCQ quizzes, flashcards with spaced repetition (SM-2 algorithm), achievements, and leaderboards.

## 📁 Project Structure

```
CP/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .env                   # Environment configuration
├── .env.example          # Environment template
├── README.md             # This file
│
├── src/                  # Source modules
│   ├── __init__.py
│   ├── db_config.py      # Database connection configuration
│   ├── achievement_system.py  # Achievement checking logic
│   └── flashcard_system.py    # Flashcard & SM-2 algorithm
│
├── templates/            # Jinja2 HTML templates
│   ├── base.html         # Base template with navigation
│   ├── index.html        # Homepage
│   ├── login.html        # Login page
│   ├── register.html     # Registration page
│   ├── quiz.html         # Quiz interface
│   ├── results.html      # Quiz results
│   ├── achievements.html # Achievements page
│   ├── flashcard_dashboard.html  # Flashcard dashboard
│   ├── deck_view.html    # Individual deck view
│   ├── study_session.html # Study session with flip cards
│   ├── mcq_categories.html # MCQ category browser
│   ├── leaderboard.html  # Points leaderboard
│   ├── admin.html        # Admin panel
│   └── errors/           # Error pages (403, 404, 500)
│
├── static/               # Static assets
│   ├── css/
│   │   └── style.css     # Main stylesheet
│   └── js/
│       └── admin.js      # Admin panel JavaScript
│
├── database/             # Database files
│   ├── COMPLETE_DATABASE_SCHEMA.sql  # Full schema
│   └── migrations/       # Migration scripts
│       ├── flashcard_migration.sql
│       ├── auth_migration.py
│       ├── migrate_achievements.py
│       ├── comprehensive_achievements_migration.py
│       ├── run_flashcard_migration.py
│       └── optimize_database.py
│
├── data/                 # Quiz data files
│   ├── physics.csv
│   ├── chemistry.csv
│   ├── biology.csv
│   └── maths.csv
│
├── tests/                # Test files
│   ├── __init__.py
│   ├── test_achievements.py
│   ├── test_comprehensive_achievements.py
│   ├── test_login.py
│   └── test_optimizations.py
│
├── scripts/              # Utility scripts
│   ├── check_achievements.py
│   ├── check_db.py
│   ├── debug_login.py
│   ├── extract_schema.py
│   ├── verify_installation.py
│   └── add_retry_champion.py
│
├── docs/                 # Documentation
│   ├── PROJECT_DOCUMENTATION.md
│   ├── CP_ANAS_DIFFERENCES.txt
│   └── information.txt
│
├── logs/                 # Application logs
│
└── archive/              # Archived/deprecated files
    ├── CP_anas/          # Reference implementation
    └── ACHIEVEMENTS_IMPLEMENTATION.py
```

## 🚀 Features

### Quiz System
- Multiple choice questions across Physics, Chemistry, Biology, and Mathematics
- Category-based question filtering
- Quiz session tracking and results history
- Question review and marked questions

### Flashcard System
- Create and manage flashcard decks
- **SM-2 Spaced Repetition Algorithm** for optimal learning
- Study sessions with flip-card interface
- Progress tracking and mastery indicators

### Achievement System
- 30+ achievements across multiple categories
- Quiz-based, streak-based, and flashcard achievements
- Points system with rewards

### Leaderboard
- Global points leaderboard
- Time-filtered rankings (All time, Monthly, Weekly)
- Achievement counts

## 🛠️ Installation

1. **Clone and setup environment:**
   ```bash
   cd CP
   python -m venv venv
   venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   copy .env.example .env
   # Edit .env with your database credentials
   ```

3. **Setup database:**
   ```bash
   mysql -u root -p < database/COMPLETE_DATABASE_SCHEMA.sql
   python database/migrations/run_flashcard_migration.py
   ```

4. **Run the application:**
   ```bash
   python app.py
   ```

5. **Access the application:**
   - Open http://localhost:5000 in your browser

## 🔧 Configuration

Edit `.env` file:
```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=mcq_flashcards
SECRET_KEY=your-secret-key
```

## 📊 Database Tables

| Table | Purpose |
|-------|---------|
| users | User accounts |
| questions | MCQ questions |
| quiz_sessions | Active quiz sessions |
| results | Quiz results |
| achievements | Achievement definitions |
| user_achievements | Unlocked achievements |
| decks | Flashcard decks |
| cards | Flashcard content |
| card_performance | SM-2 tracking |
| study_log | Study session logs |
| mcq_categories | MCQ categories |

## 🧪 Running Tests

```bash
cd CP
python -m pytest tests/
```

## 📝 License

This project is for educational purposes as part of the DBMS course project.

## 👥 Contributors

- VIT SY Sem 3 DBMS Course Project
