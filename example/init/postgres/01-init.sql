-- PostgreSQL initialization script for DBAnu
-- Creates the books table and inserts sample data
-- Theme: Fantasy Books

CREATE TABLE IF NOT EXISTS books (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255) NOT NULL,
    year INTEGER NOT NULL
);

-- Insert sample Fantasy books
INSERT INTO books (title, author, year) VALUES
    ('The Hobbit', 'J.R.R. Tolkien', 1937),
    ('The Fellowship of the Ring', 'J.R.R. Tolkien', 1954),
    ('Harry Potter and the Philosopher''s Stone', 'J.K. Rowling', 1997),
    ('The Name of the Wind', 'Patrick Rothfuss', 2007),
    ('A Game of Thrones', 'George R.R. Martin', 1996),
    ('The Way of Kings', 'Brandon Sanderson', 2010),
    ('The Lion, the Witch and the Wardrobe', 'C.S. Lewis', 1950)
ON CONFLICT DO NOTHING;