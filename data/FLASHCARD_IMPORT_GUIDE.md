# Flashcard CSV Import Guide

## CSV Format

The flashcard system accepts CSV files with the following format:

```csv
Question,Answer
What is the capital of France?,Paris
What is 2 + 2?,4
```

### Supported Column Names

The system automatically detects and maps the following column names:
- **Question columns**: `Question`, `question`, `front_content`
- **Answer columns**: `Answer`, `answer`, `back_content`

## Import Methods

### Method 1: Command Line Script (Recommended for bulk import)

Use the provided script to import all flashcard CSV files:

```bash
python scripts/import_flashcards.py
```

This script will:
1. Find or create an admin user
2. Create decks for each subject (Biology, Chemistry, Physics, Mathematics)
3. Import all flashcards from the CSV files in the `data/` folder
4. Display progress and results

### Method 2: Web Interface

1. Log in to the application
2. Go to the Flashcard Dashboard
3. Create a new deck or select an existing deck
4. Click on "Upload CSV" 
5. Select your CSV file
6. The cards will be imported automatically

API Endpoint: `POST /decks/<deck_id>/upload-csv`

## Available Flashcard Files

The following flashcard CSV files are included in `data/`:

- **biology_flashcards.csv** - 30 biology questions
- **chemistry_flashcards.csv** - 30 chemistry questions  
- **physics_flashcards.csv** - 30 physics questions
- **maths_flashcards.csv** - 30 mathematics questions

## Creating Your Own Flashcard CSV

1. Create a new CSV file with `Question,Answer` headers
2. Add your flashcards, one per row
3. Save the file with UTF-8 encoding
4. Import using either method above

### Example CSV:

```csv
Question,Answer
"What is photosynthesis?","The process by which plants convert light energy into chemical energy"
"What is the chemical symbol for water?","H2O"
"Who wrote Romeo and Juliet?","William Shakespeare"
```

### Tips:

- Use quotes around fields that contain commas or special characters
- Keep questions and answers concise for better studying
- Ensure UTF-8 encoding for special characters
- Avoid extremely long text (keep under 500 characters per field)

## Spaced Repetition

Once imported, flashcards use the SM-2 spaced repetition algorithm:
- **Forgot**: Review in < 1 minute
- **Hard**: Review in < 10 minutes
- **Good**: Review in 1 day
- **Easy**: Review in 4+ days

The system automatically schedules reviews based on your performance!
