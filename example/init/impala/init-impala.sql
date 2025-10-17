-- Impala initialization script for DBAnu
-- Creates database and books table with sample data

CREATE DATABASE IF NOT EXISTS dbanu_db;
USE dbanu_db;

CREATE TABLE IF NOT EXISTS books (
    id INT,
    title STRING,
    author STRING,
    year INT
)
STORED AS PARQUET;

-- Insert sample data
INSERT INTO books VALUES
    (1, 'The Great Gatsby', 'F. Scott Fitzgerald', 1925),
    (2, 'To Kill a Mockingbird', 'Harper Lee', 1960),
    (3, '1984', 'George Orwell', 1949),
    (4, 'Pride and Prejudice', 'Jane Austen', 1813),
    (5, 'The Catcher in the Rye', 'J.D. Salinger', 1951);