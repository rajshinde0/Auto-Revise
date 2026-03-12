# 🎓 AutoRevise - Complete Project Documentation

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Features](#features)
4. [Technology Stack](#technology-stack)
5. [Database Schema](#database-schema)
6. [File Structure](#file-structure)
7. [Setup & Installation](#setup--installation)
8. [User Workflows](#user-workflows)
9. [API Endpoints](#api-endpoints)
10. [Troubleshooting](#troubleshooting)

---

## 📖 Project Overview

**AutoRevise** is a comprehensive web-based learning management system that helps students study effectively using flashcards and MCQ (Multiple Choice Questions) with spaced repetition algorithms.

### Key Features:
- ✅ **User Authentication** - Secure login/registration system
- ✅ **Flashcard System** - Create, study, and review flashcards
- ✅ **MCQ Practice** - Category-based multiple choice questions
- ✅ **Spaced Repetition** - Smart scheduling for optimal learning
- ✅ **Gamification** - Points, streaks, and achievements
- ✅ **Admin Panel** - Bulk upload flashcards and MCQs
- ✅ **Progress Tracking** - Detailed statistics and performance metrics

---

## 🏗️ System Architecture

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENT SIDE                          │
│                     (Frontend - HTML/CSS/JS)                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ Login/Register│  │  Dashboard   │  │ Study Session│    │
│  │   Pages       │  │   Page       │  │    Page      │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ MCQ Practice │  │ Achievements │  │  Admin Panel │    │
│  │   (Category) │  │    Page      │  │   (Upload)   │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                            ↕ HTTP/AJAX
                    (Fetch API with CORS)
┌─────────────────────────────────────────────────────────────┐
│                        SERVER SIDE                          │
│                    (Backend - Flask/Python)                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │     Auth     │  │   Flashcard  │  │     MCQ      │    │
│  │  Endpoints   │  │  Endpoints   │  │  Endpoints   │    │
│  │  /login      │  │  /decks      │  │ /mcq/upload  │    │
│  │  /register   │  │  /cards      │  │ /mcq/category│    │
│  │  /logout     │  │  /study      │  │ /mcq/check   │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ Achievement  │  │   Session    │  │    Admin     │    │
│  │  Endpoints   │  │  Management  │  │  Decorators  │    │
│  │ /achievements│  │   (Cookies)  │  │ @login_req   │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                            ↕ SQL
                   (MySQL Connector)
┌─────────────────────────────────────────────────────────────┐
│                       DATABASE LAYER                        │
│                         (MySQL 8.x)                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │    Users     │  │    Decks     │  │    Cards     │    │
│  │  (Auth Data) │  │ (Flashcard   │  │  (Front/Back │    │
│  │              │  │  Collections)│  │   Content)   │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │MCQ_Questions │  │MCQ_Categories│  │MCQ_Performance│   │
│  │ (MCQ Data)   │  │  (Biology,   │  │(User Attempts)│   │
│  │              │  │   Physics)   │  │              │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │CardPerformance│ │ Achievements │  │UserAchievements│  │
│  │(Spaced Rep.) │  │  (Badges)    │  │   (Earned)   │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Features

### 1. User Authentication
- **Registration**: Email, username, password (bcrypt hashed)
- **Login**: Session-based authentication with cookies
- **Session Management**: Persistent sessions across page reloads
- **Logout**: Clean session termination

### 2. Flashcard System
- **Deck Management**: Create, edit, delete decks
- **Card Creation**: Add flashcards with front/back content
- **CSV Import**: Bulk upload flashcards via CSV
- **Study Mode**: Interactive flashcard review
- **Spaced Repetition**: SM-2 algorithm for optimal review scheduling

### 3. MCQ System
- **10 Categories**: Biology, Physics, Chemistry, Math, CS, History, Geography, English, General Knowledge, Other
- **Category Browse**: Visual grid with icons and question counts
- **Practice Mode**: Category-specific question practice
- **Instant Feedback**: Immediate right/wrong with explanations
- **CSV Upload**: Admin bulk upload with category support

### 4. Gamification
- **Points System**: Earn points for correct answers
- **Achievements**: Unlock badges for milestones
- **Streaks**: Daily study streaks
- **Leaderboard**: (Planned feature)

### 5. Admin Features
- **Flashcard Upload**: CSV bulk import
- **MCQ Upload**: CSV bulk import with category selection
- **User Management**: Make users admin
- **Upload Logs**: Track all uploads

---

## 💻 Technology Stack

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| HTML5 | - | Structure and markup |
| CSS3 | - | Styling and animations |
| JavaScript (Vanilla) | ES6+ | Client-side logic |
| Font Awesome | 6.4.0 | Icons |
| Papa Parse | 5.3.0 | CSV parsing |

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.x | Server-side language |
| Flask | 2.x | Web framework |
| Flask-CORS | - | CORS handling |
| bcrypt | - | Password hashing |
| MySQL Connector | 8.x | Database driver |

### Database
| Technology | Version | Purpose |
|------------|---------|---------|
| MySQL | 8.x | Relational database |

### Development Tools
| Tool | Purpose |
|------|---------|
| VS Code | Code editor |
| Live Server | Frontend development server |
| Git | Version control |

---

## 🗄️ Database Schema

### Complete ERD (Entity Relationship Diagram)

```
┌──────────────────────┐
│      Users           │
├──────────────────────┤
│ PK user_id           │
│    username          │
│    email             │
│    password_hash     │
│    points            │
│    is_admin          │──┐
│    created_at        │  │
└──────────────────────┘  │
         │                │
         │ 1              │ 1
         │                │
         │ *              │ *
┌────────▼──────────┐  ┌──▼─────────────────┐
│     Decks         │  │  MCQ_Upload_Log    │
├───────────────────┤  ├────────────────────┤
│ PK deck_id        │  │ PK upload_id       │
│ FK user_id        │  │ FK admin_id        │
│    deck_name      │  │ FK category_id     │
│    description    │  │    filename        │
│    created_at     │──┐│    total_questions │
└───────────────────┘  ││    successful      │
         │             ││    failed          │
         │ 1           │└────────────────────┘
         │             │
         │ *           │
┌────────▼──────────┐  │
│      Cards        │  │
├───────────────────┤  │
│ PK card_id        │  │
│ FK deck_id        │  │
│    front_content  │  │
│    back_content   │  │
│    created_at     │──┘
└───────────────────┘
         │
         │ 1
         │
         │ *
┌────────▼──────────────┐
│  CardPerformance      │
├───────────────────────┤
│ PK performance_id     │
│ FK user_id            │
│ FK card_id            │
│    next_review_date   │
│    interval           │
│    ease_factor        │
└───────────────────────┘

┌──────────────────────┐
│  MCQ_Categories      │
├──────────────────────┤
│ PK category_id       │
│    category_name     │
│    description       │
│    icon              │
│    created_at        │
└──────────────────────┘
         │
         │ 1
         │
         │ *
┌────────▼──────────┐
│  MCQ_Questions    │
├───────────────────┤
│ PK mcq_id         │
│ FK deck_id        │
│ FK category_id    │
│ FK created_by     │
│    question_text  │
│    option_a       │
│    option_b       │
│    option_c       │
│    option_d       │
│    correct_option │
│    explanation    │
│    difficulty     │
│    created_at     │
└───────────────────┘
         │
         │ 1
         │
         │ *
┌────────▼──────────────┐
│  MCQ_Performance      │
├───────────────────────┤
│ PK mcq_performance_id │
│ FK user_id            │
│ FK mcq_id             │
│    last_attempt_date  │
│    times_attempted    │
│    times_correct      │
│    next_review_date   │
└───────────────────────┘

┌──────────────────────┐
│   Achievements       │
├──────────────────────┤
│ PK achievement_id    │
│    achievement_name  │
│    description       │
│    icon              │
│    required_points   │
│    created_at        │
└──────────────────────┘
         │
         │ 1
         │
         │ *
┌────────▼──────────────┐
│  UserAchievements     │
├───────────────────────┤
│ PK user_achieve_id    │
│ FK user_id            │
│ FK achievement_id     │
│    unlocked_at        │
└───────────────────────┘

┌──────────────────────┐
│     StudyLog         │
├──────────────────────┤
│ PK log_id            │
│ FK user_id           │
│    study_date        │
│    cards_reviewed    │
│    session_duration  │
└──────────────────────┘
```

### Table Details

#### 1. **Users** (Core user data)
- `user_id` - Primary key, auto-increment
- `username` - Unique username
- `email` - Unique email address
- `password_hash` - bcrypt hashed password
- `points` - Total points earned
- `is_admin` - Boolean flag for admin privileges
- `created_at` - Registration timestamp

#### 2. **Decks** (Flashcard collections)
- `deck_id` - Primary key
- `user_id` - Foreign key to Users
- `deck_name` - Name of the deck
- `description` - Optional description
- `created_at` - Creation timestamp

#### 3. **Cards** (Individual flashcards)
- `card_id` - Primary key
- `deck_id` - Foreign key to Decks
- `front_content` - Question/front side
- `back_content` - Answer/back side
- `created_at` - Creation timestamp

#### 4. **CardPerformance** (Spaced repetition data)
- `performance_id` - Primary key
- `user_id` - Foreign key to Users
- `card_id` - Foreign key to Cards
- `next_review_date` - When to review next
- `interval` - Days until next review
- `ease_factor` - SM-2 algorithm factor (default 2.5)

#### 5. **MCQ_Categories** (Subject categories)
- `category_id` - Primary key
- `category_name` - Category name (Biology, Physics, etc.)
- `description` - Category description
- `icon` - Font Awesome icon class
- `created_at` - Creation timestamp

#### 6. **MCQ_Questions** (Multiple choice questions)
- `mcq_id` - Primary key
- `deck_id` - Foreign key to Decks
- `category_id` - Foreign key to MCQ_Categories
- `created_by` - Foreign key to Users (admin who created)
- `question_text` - The question
- `option_a, option_b, option_c, option_d` - Answer choices
- `correct_option` - Correct answer (A/B/C/D)
- `explanation` - Explanation for answer
- `difficulty` - easy/medium/hard
- `created_at` - Creation timestamp

#### 7. **MCQ_Performance** (User MCQ attempts)
- `mcq_performance_id` - Primary key
- `user_id` - Foreign key to Users
- `mcq_id` - Foreign key to MCQ_Questions
- `last_attempt_date` - Last attempt timestamp
- `times_attempted` - Total attempts
- `times_correct` - Correct attempts
- `next_review_date` - Next review date (spaced repetition)

#### 8. **Achievements** (Available badges)
- `achievement_id` - Primary key
- `achievement_name` - Name of achievement
- `description` - What it's for
- `icon` - Icon class
- `required_points` - Points needed to unlock
- `created_at` - Creation timestamp

#### 9. **UserAchievements** (Earned badges)
- `user_achieve_id` - Primary key
- `user_id` - Foreign key to Users
- `achievement_id` - Foreign key to Achievements
- `unlocked_at` - When unlocked

#### 10. **StudyLog** (Study session tracking)
- `log_id` - Primary key
- `user_id` - Foreign key to Users
- `study_date` - Date of study session
- `cards_reviewed` - Number of cards reviewed
- `session_duration` - Time spent (minutes)

#### 11. **MCQ_Upload_Log** (Admin upload tracking)
- `upload_id` - Primary key
- `admin_id` - Foreign key to Users
- `category_id` - Foreign key to MCQ_Categories
- `filename` - Uploaded file name
- `total_questions` - Total in file
- `successful_imports` - Successfully imported
- `failed_imports` - Failed imports
- `upload_date` - Upload timestamp

---

## 📁 File Structure

```
D:\New folder\DBMS\
│
├── Backened/
│   ├── App1.py                          ⭐ Main Flask application
│   ├── requirements.txt                 ⭐ Python dependencies
│   ├── schema2.sql                      ⭐ Main database schema
│   ├── schema_mcq_update.sql            ⭐ MCQ tables schema
│   ├── schema_mcq_categories.sql        ⭐ Categories schema
│   ├── run_mcq_schema_safe.py          ⭐ Safe MCQ schema updater
│   ├── run_mcq_categories_schema.py    ⭐ Safe categories updater
│   ├── make_admin.py                    ⭐ Make user admin utility
│   ├── sample_mcqs.csv                  📄 Sample MCQ data
│   ├── sample_biology_mcqs.csv          📄 Biology MCQs sample
│   └── sample_physics_mcqs.csv          📄 Physics MCQs sample
│
├── Frontened 1/
│   ├── index.html                       ⭐ Landing page
│   ├── login-page.html                  ⭐ Login page
│   ├── register-page.html               ⭐ Registration page
│   ├── dashboard-connected.html         ⭐ Main dashboard
│   ├── deck-view.html                   ⭐ Deck management
│   ├── study-session.html               ⭐ Flashcard study
│   ├── study.html                       📄 (Old study page)
│   ├── achievements.html                ⭐ Achievements page
│   ├── admin-mcq-upload.html            ⭐ Admin MCQ upload
│   ├── mcq-practice.html                ⭐ MCQ practice (categories)
│   ├── test-integration.html            📄 Test page
│   ├── mcq-debug.html                   🔧 Debug tool
│   │
│   ├── css/
│   │   ├── style.css                    ⭐ Landing page styles
│   │   ├── auth.css                     ⭐ Login/register styles
│   │   ├── dashboard.css                ⭐ Main app styles
│   │   ├── deck-view.css                ⭐ Deck view styles
│   │   ├── study-session.css            ⭐ Study session styles
│   │   └── achievements.css             ⭐ Achievements styles
│   │
│   └── js/
│       ├── api-app1.js                  ⭐ API client class
│       ├── dashboard-connected.js       ⭐ Dashboard logic
│       ├── deck-view-connected.js       ⭐ Deck view logic
│       ├── study-session-connected.js   ⭐ Study session logic
│       └── achievements-connected.js    ⭐ Achievements logic
│
└── Documentation/
    ├── ARCHITECTURE.md                   📄 Architecture overview
    ├── CHECKLIST.md                      📄 Feature checklist
    ├── CONNECTION_GUIDE.md               📄 Connection guide
    ├── QUICK_START.md                    📄 Quick start guide
    ├── SUMMARY.md                        📄 Project summary
    ├── MCQ_FEATURE_GUIDE.md              📄 MCQ feature docs
    ├── MCQ_CSV_FORMAT.md                 📄 CSV format guide
    ├── MCQ_IMPLEMENTATION_SUMMARY.md     📄 MCQ implementation
    ├── MCQ_CHECKLIST.md                  📄 MCQ testing checklist
    ├── MCQ_CATEGORIES_GUIDE.md           📄 Categories guide
    └── IMPLEMENTATION_SUMMARY_CATEGORIES.md 📄 Categories summary

Legend:
⭐ = Essential/Active file
📄 = Documentation/Reference
🔧 = Debug/Utility tool
```

---

## 🚀 Setup & Installation

### Prerequisites
- Python 3.8 or higher
- MySQL 8.0 or higher
- VS Code (recommended) with Live Server extension
- Web browser (Chrome, Firefox, Edge)

### Step-by-Step Setup

#### 1. **Database Setup**

```bash
# 1. Open MySQL Command Line or MySQL Workbench

# 2. Create database and tables
mysql> source D:\New folder\DBMS\Backened\schema2.sql

# 3. Add MCQ tables
mysql> source D:\New folder\DBMS\Backened\schema_mcq_update.sql

# 4. Add Categories (OR use Python script)
cd "D:\New folder\DBMS\Backened"
python run_mcq_categories_schema.py
```

#### 2. **Backend Setup**

```bash
# 1. Navigate to backend folder
cd "D:\New folder\DBMS\Backened"

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Verify database connection in App1.py (lines 17-22)
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Root123',  # ← Change to your MySQL password
    'database': 'autorevise_db'
}

# 4. Start Flask server
python App1.py

# Expected output:
# INFO:__main__:Starting AutoRevise backend on port 5000
# * Running on http://127.0.0.1:5000
```

#### 3. **Frontend Setup**

```bash
# 1. Open project in VS Code
code "D:\New folder\DBMS"

# 2. Install Live Server extension in VS Code
# (Search for "Live Server" in Extensions)

# 3. Open any HTML file in "Frontened 1" folder

# 4. Right-click → "Open with Live Server"
# OR click "Go Live" in VS Code status bar

# Frontend will open at: http://127.0.0.1:5501
```

#### 4. **Create First Admin User**

**Option A: Via Database**
```sql
-- Register normally through website, then:
UPDATE Users SET is_admin = TRUE WHERE username = 'yourusername';
```

**Option B: Via Python Script**
```bash
cd "D:\New folder\DBMS\Backened"
python make_admin.py
# Follow prompts to select user
```

#### 5. **Test the Application**

```bash
# 1. Open browser: http://127.0.0.1:5501/index.html

# 2. Register a new account

# 3. Login with credentials

# 4. You should see the dashboard!
```

---

## 👥 User Workflows

### User Workflow Flowchart

```
START
  │
  ├─→ [New User] → Register → Login → Dashboard
  │                                       │
  └─→ [Existing User] → Login ───────────┘
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    │                     │                     │
                    ▼                     ▼                     ▼
            ┌───────────────┐   ┌─────────────────┐   ┌──────────────┐
            │   Flashcards  │   │   MCQ Practice  │   │ Achievements │
            └───────────────┘   └─────────────────┘   └──────────────┘
                    │                     │                     │
        ┌───────────┼───────────┐        │                     │
        │           │           │        │                     │
        ▼           ▼           ▼        ▼                     ▼
    ┌──────┐  ┌─────────┐  ┌───────┐  ┌──────────┐   ┌──────────────┐
    │Create│  │ Study   │  │ Upload│  │ Browse   │   │ View Badges  │
    │ Deck │  │ Session │  │  CSV  │  │Categories│   │ Track Points │
    └──────┘  └─────────┘  └───────┘  └──────────┘   └──────────────┘
        │           │           │        │                     │
        │           │           │        ▼                     │
        │           │           │   ┌──────────┐              │
        │           │           │   │ Practice │              │
        │           │           │   │Questions │              │
        │           │           │   └──────────┘              │
        │           │           │        │                     │
        │           ▼           │        ▼                     │
        │    ┌──────────────┐  │   ┌─────────┐              │
        │    │ Spaced Rep.  │  │   │ Instant │              │
        │    │  Algorithm   │  │   │Feedback │              │
        │    └──────────────┘  │   └─────────┘              │
        │           │           │        │                     │
        └───────────┴───────────┴────────┴─────────────────────┘
                                │
                                ▼
                        ┌──────────────┐
                        │ Earn Points  │
                        │   & Badges   │
                        └──────────────┘
                                │
                                ▼
                              [END]
```

### Admin Workflow

```
Admin Login
    │
    ├─→ Dashboard (Admin Link Visible)
    │
    └─→ Admin Panel
            │
            ├─→ Upload Flashcards (CSV)
            │     │
            │     ├─→ Select Deck
            │     ├─→ Choose CSV File
            │     ├─→ Validate Format
            │     └─→ Import Cards
            │
            └─→ Upload MCQs (CSV)
                  │
                  ├─→ Select Category (Biology, Physics, etc.)
                  ├─→ Choose CSV File
                  ├─→ Validate Format
                  ├─→ Import Questions
                  └─→ View Upload Log
```

---

## 🔌 API Endpoints

### Complete API Reference

#### **Authentication Endpoints**

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/register` | ❌ | Create new user account |
| POST | `/login` | ❌ | Login and create session |
| POST | `/logout` | ✅ | Logout and destroy session |
| GET | `/me` | ✅ | Get current user info |

**Example: Login**
```javascript
POST /login
Body: {
  "email": "user@example.com",
  "password": "password123"
}
Response: {
  "message": "Login successful",
  "user": {
    "user_id": 1,
    "username": "john",
    "email": "user@example.com",
    "points": 250,
    "is_admin": false
  }
}
```

---

#### **Deck Endpoints**

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/decks` | ✅ | Get all user's decks |
| POST | `/decks` | ✅ | Create new deck |
| GET | `/decks/<id>` | ✅ | Get specific deck |
| PUT | `/decks/<id>` | ✅ | Update deck |
| DELETE | `/decks/<id>` | ✅ | Delete deck |

---

#### **Card Endpoints**

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/decks/<id>/cards` | ✅ | Get cards in deck |
| POST | `/decks/<id>/cards` | ✅ | Add card to deck |
| PUT | `/cards/<id>` | ✅ | Update card |
| DELETE | `/cards/<id>` | ✅ | Delete card |
| POST | `/cards/upload` | ✅ | Bulk upload CSV |

---

#### **Study Endpoints**

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/study/due` | ✅ | Get cards due for review |
| POST | `/study/review` | ✅ | Submit card review (Easy/Medium/Hard) |
| GET | `/study/stats` | ✅ | Get study statistics |

---

#### **MCQ Endpoints**

| Method | Endpoint | Auth | Admin | Description |
|--------|----------|------|-------|-------------|
| GET | `/mcq/categories` | ✅ | ❌ | Get all categories |
| GET | `/mcq/category/<id>` | ✅ | ❌ | Get MCQs by category |
| POST | `/mcq/upload` | ✅ | ✅ | Upload MCQs (CSV) |
| POST | `/mcq/<id>/check` | ✅ | ❌ | Check answer |
| GET | `/mcq/study-session` | ✅ | ❌ | Get MCQs for study |
| GET | `/mcq/stats` | ✅ | ❌ | Get MCQ statistics |

**Example: Check MCQ Answer**
```javascript
POST /mcq/123/check
Body: {
  "selected_option": "B"
}
Response: {
  "correct": true,
  "explanation": "Mitochondria are the powerhouse of the cell...",
  "points_awarded": 5
}
```

---

#### **Achievement Endpoints**

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/achievements` | ✅ | Get all achievements |
| GET | `/achievements/user` | ✅ | Get user's achievements |

---

## 🎨 Detailed Features Explanation

### 1. **Spaced Repetition Algorithm (SM-2)**

The system uses the SuperMemo SM-2 algorithm for optimal card scheduling:

```python
# Algorithm Logic
def calculate_next_review(quality, interval, ease_factor):
    """
    quality: 0-5 (0=wrong, 3=hard, 4=medium, 5=easy)
    interval: days since last review
    ease_factor: difficulty multiplier (starts at 2.5)
    """
    
    if quality >= 3:  # Correct answer
        if interval == 0:
            interval = 1
        elif interval == 1:
            interval = 6
        else:
            interval = interval * ease_factor
        
        ease_factor = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    else:  # Wrong answer
        interval = 1
        ease_factor = max(1.3, ease_factor)
    
    return interval, ease_factor
```

**User Experience:**
- ✅ **Easy** → See card in 6+ days
- ⚠️ **Hard** → See card in 1-3 days
- ❌ **Wrong** → See card again tomorrow

---

### 2. **Points & Gamification System**

| Action | Points Earned |
|--------|---------------|
| Correct flashcard (Easy) | 5 points |
| Correct flashcard (Medium) | 3 points |
| Correct flashcard (Hard) | 2 points |
| Correct MCQ | 5 points |
| Daily study streak | 10 points/day |
| Unlock achievement | 100 bonus points |

**Achievements:**
- 🎯 First Steps (10 points)
- 📚 Study Enthusiast (100 points)
- 🔥 Week Streak (7 day streak)
- 🏆 Century Club (1000 points)

---

### 3. **MCQ Category System**

**Categories with Icons:**
```
🔬 Biology        - Life sciences
⚛️  Physics        - Mechanics & forces
🧪 Chemistry      - Chemical reactions
🔢 Mathematics    - Algebra & calculus
💻 Computer Science - Programming
🏛️  History        - World history
🌍 Geography      - World regions
📖 English        - Literature
🧠 General Knowledge - Trivia
❓ Other          - Uncategorized
```

**Upload Process:**
1. Admin selects category from dropdown
2. Uploads CSV file
3. System validates format
4. Questions auto-tagged with category
5. Available immediately to users

---

## 🛠️ Troubleshooting

### Common Issues & Solutions

#### Issue 1: "Connection Refused" / "ERR_CONNECTION_REFUSED"
**Cause:** Backend server not running

**Solution:**
```bash
cd "D:\New folder\DBMS\Backened"
python App1.py
```

---

#### Issue 2: "401 Unauthorized" errors
**Cause:** Session expired or not logged in

**Solution:**
1. Logout completely
2. Clear browser cookies (F12 → Application → Cookies)
3. Login again

---

#### Issue 3: "CORS Error"
**Cause:** Frontend and backend on different origins

**Solution:**
- Backend runs on: `http://127.0.0.1:5000`
- Frontend MUST use: `http://127.0.0.1:5501` (via Live Server)
- DO NOT open files directly (`file:///` won't work)

---

#### Issue 4: "Categories not loading"
**Cause:** Database schema not updated

**Solution:**
```bash
cd "D:\New folder\DBMS\Backened"
python run_mcq_categories_schema.py
```

---

#### Issue 5: "Admin link not showing"
**Cause:** User not marked as admin

**Solution:**
```bash
# Option 1: Python script
python make_admin.py

# Option 2: MySQL directly
UPDATE Users SET is_admin = TRUE WHERE user_id = 1;
```

---

## 📊 System Flow Diagrams

### Complete User Journey

```
┌─────────────────────────────────────────────────────────────┐
│                    AUTOREVISE SYSTEM FLOW                   │
└─────────────────────────────────────────────────────────────┘

[Landing Page]
      │
      ├─→ New User → [Register] → [Email Verification] → [Login]
      │                                                       │
      └─→ Existing → [Login] ────────────────────────────────┘
                        │
                        ▼
                 ┌──────────────┐
                 │  Dashboard   │ ← User's home
                 └──────────────┘
                        │
        ┌───────────────┼───────────────┬──────────────┐
        │               │               │              │
        ▼               ▼               ▼              ▼
   ┌────────┐    ┌──────────┐    ┌─────────┐   ┌──────────┐
   │ Decks  │    │   MCQ    │    │  Study  │   │Achievements│
   │ (CRUD) │    │Practice  │    │ Session │   │  & Stats  │
   └────────┘    └──────────┘    └─────────┘   └──────────┘
        │               │               │              │
        │               │               │              │
┌───────┼───────┐      │       ┌───────┼──────┐      │
│       │       │      │       │       │      │      │
▼       ▼       ▼      ▼       ▼       ▼      ▼      ▼
Create  Edit  Delete  Browse  Review  Rate  View   Track
Deck   Cards  Deck    Category Cards  Difficulty Badge Points

                 All paths lead to:
                        │
                        ▼
                ┌──────────────┐
                │ Points System│
                └──────────────┘
                        │
                        ▼
                ┌──────────────┐
                │ Achievements │
                └──────────────┘
```

---

## 📝 Quick Reference

### CSV Upload Formats

#### Flashcard CSV Format
```csv
front_content,back_content
"What is Python?","A high-level programming language"
"What is Flask?","A Python web framework"
```

#### MCQ CSV Format (with category)
```csv
question_text,option_a,option_b,option_c,option_d,correct_option,explanation,difficulty,deck_id,category_id
"What is the capital of France?",London,Berlin,Paris,Madrid,C,"Paris is the capital of France",easy,1,7
```

---

### Port Configuration

| Service | Port | URL |
|---------|------|-----|
| Backend (Flask) | 5000 | http://127.0.0.1:5000 |
| Frontend (Live Server) | 5501 | http://127.0.0.1:5501 |
| MySQL | 3306 | localhost:3306 |

---

### Default Credentials

**Database:**
- Host: `localhost`
- User: `root`
- Password: `Root123` (change in App1.py)
- Database: `autorevise_db`

**First User:**
- Register through website
- Then make admin using `make_admin.py`

---

## 🎓 Educational Benefits

### For Students:
✅ **Spaced Repetition** - Proven to improve long-term retention
✅ **Active Recall** - Better than passive reading
✅ **Gamification** - Makes learning fun and motivating
✅ **Progress Tracking** - See your improvement over time
✅ **Category Organization** - Structured learning by subject

### For Teachers/Admins:
✅ **Bulk Upload** - Add hundreds of questions quickly
✅ **Category Management** - Organize by subject
✅ **Upload Tracking** - Monitor what's been added
✅ **Student Progress** - (Future: View student stats)

---

## 🚀 Future Enhancements

Planned features for next version:
- [ ] Dark mode toggle
- [ ] Export progress as PDF
- [ ] Shared decks (public library)
- [ ] Mobile app (React Native)
- [ ] AI-generated explanations
- [ ] Voice narration for cards
- [ ] Collaborative study rooms
- [ ] Advanced analytics dashboard
- [ ] Integration with Google Classroom

---

## 📞 Support

For issues or questions:
1. Check this documentation
2. Check `mcq-debug.html` for diagnostic tools
3. Review browser console (F12)
4. Check backend logs in terminal

---

**AutoRevise** - Smart Learning, Better Results 🎓
