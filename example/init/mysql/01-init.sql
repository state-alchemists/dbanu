-- MySQL initialization script for DBAnu
-- Creates the books table and inserts sample data
-- Theme: Science Fiction Books

CREATE TABLE IF NOT EXISTS books (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255) NOT NULL,
    year INT NOT NULL
);

-- Insert sample Science Fiction books
INSERT IGNORE INTO books (title, author, year) VALUES
    ('Dune', 'Frank Herbert', 1965),
    ('Foundation', 'Isaac Asimov', 1951),
    ('Neuromancer', 'William Gibson', 1984),
    ('The Hitchhiker''s Guide to the Galaxy', 'Douglas Adams', 1979),
    ('Ender''s Game', 'Orson Scott Card', 1985),
    ('The Martian', 'Andy Weir', 2011),
    ('Ready Player One', 'Ernest Cline', 2011);