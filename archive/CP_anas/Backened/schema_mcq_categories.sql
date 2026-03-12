

USE autorevise_db;

-- 1. Create MCQ_Categories table
CREATE TABLE IF NOT EXISTS MCQ_Categories (
    category_id INT PRIMARY KEY AUTO_INCREMENT,
    category_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT NULL,
    icon VARCHAR(50) NULL, -- for UI icons like 'fa-microscope', 'fa-atom', etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_category_name (category_name)
) ENGINE=InnoDB;

-- 2. Add category_id to MCQ_Questions table
ALTER TABLE MCQ_Questions 
ADD COLUMN category_id INT NULL AFTER deck_id,
ADD FOREIGN KEY (category_id) REFERENCES MCQ_Categories(category_id) ON DELETE SET NULL,
ADD INDEX idx_category (category_id);

-- 3. Insert default categories
INSERT INTO MCQ_Categories (category_name, description, icon) VALUES
('Biology', 'Life sciences, anatomy, genetics, ecology', 'fa-microscope'),
('Physics', 'Mechanics, thermodynamics, electromagnetism, optics', 'fa-atom'),
('Chemistry', 'Organic, inorganic, physical chemistry', 'fa-flask'),
('Mathematics', 'Algebra, calculus, geometry, statistics', 'fa-calculator'),
('Computer Science', 'Programming, algorithms, data structures', 'fa-laptop-code'),
('History', 'World history, civilizations, historical events', 'fa-landmark'),
('Geography', 'Physical and human geography, world regions', 'fa-globe-americas'),
('English', 'Literature, grammar, composition', 'fa-book'),
('General Knowledge', 'Miscellaneous topics and trivia', 'fa-brain'),
('Other', 'Uncategorized questions', 'fa-question-circle')
ON DUPLICATE KEY UPDATE category_name=category_name;


ALTER TABLE MCQ_Upload_Log
ADD COLUMN category_id INT NULL AFTER filename,
ADD FOREIGN KEY (category_id) REFERENCES MCQ_Categories(category_id) ON DELETE SET NULL;
