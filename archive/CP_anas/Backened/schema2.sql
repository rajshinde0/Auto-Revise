-- ==========================================================
-- AutoRevise System: Database 
-- ==========================================================
CREATE DATABASE autorevise_db;
USE autorevise_db;


CREATE TABLE Users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    points INT NOT NULL DEFAULT 0 
) ENGINE=InnoDB;

CREATE TABLE Decks (
    deck_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    deck_name VARCHAR(100) NOT NULL,
    description TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE Cards (
    card_id INT PRIMARY KEY AUTO_INCREMENT,
    deck_id INT NOT NULL,
    front_content TEXT NOT NULL,
    back_content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (deck_id) REFERENCES Decks(deck_id) ON DELETE CASCADE
) ENGINE=InnoDB;


CREATE TABLE CardPerformance (
    performance_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    card_id INT NOT NULL,
    next_review_date DATE NOT NULL,
    `interval` INT NOT NULL DEFAULT 1, 
    ease_factor DECIMAL(4,2) NOT NULL DEFAULT 2.50,
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (card_id) REFERENCES Cards(card_id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_card (user_id, card_id)
) ENGINE=InnoDB;



-- A. StudyLog Table
-- Tracks daily study sessions to enable features like study streaks.
CREATE TABLE IF NOT EXISTS StudyLog (
    log_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    study_date DATE NOT NULL,
    cards_reviewed INT NOT NULL DEFAULT 0,
    UNIQUE KEY unique_user_day (user_id, study_date), 
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- B. Achievements Reference Table
-- This table holds all possible achievements users can earn.
CREATE TABLE IF NOT EXISTS Achievements (
    achievement_id INT PRIMARY KEY AUTO_INCREMENT,
    name           VARCHAR(100) NOT NULL UNIQUE,
    description    VARCHAR(255) NOT NULL,
    icon_url       VARCHAR(255) NULL 
);

-- C. UserAchievements Table
-- This table links users to the achievements they have earned.
CREATE TABLE IF NOT EXISTS UserAchievements (
    user_id        INT NOT NULL,
    achievement_id INT NOT NULL,
    earned_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, achievement_id), 
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (achievement_id) REFERENCES Achievements(achievement_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- D. Pre-populate some achievements relevant to a study app
INSERT INTO Achievements (name, description) VALUES
('First Steps', 'Create your very first deck.'),
('Card Collector', 'Create a total of 50 cards.'),
('Knowledge Builder', 'Create a total of 250 cards.'),
('Dedicated Learner', 'Complete your first study session.'),
('7-Day Streak', 'Study for 7 days in a row.'),
('30-Day Streak', 'Study for 30 days in a row.');



SELECT 'Database and all tables created successfully!' AS Status;

SHOW TABLES;