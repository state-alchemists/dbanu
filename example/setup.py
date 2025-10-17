import sqlite3

from example.config import SQLITE_DB_PATH


def setup_sqlite():
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    # Create books table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            year INTEGER NOT NULL
        )
        """
    )
    # Insert sample data - Classic Literature theme
    books = [
        (1, "The Great Gatsby", "F. Scott Fitzgerald", 1925),
        (2, "To Kill a Mockingbird", "Harper Lee", 1960),
        (3, "1984", "George Orwell", 1949),
        (4, "Pride and Prejudice", "Jane Austen", 1813),
        (5, "The Catcher in the Rye", "J.D. Salinger", 1951),
        (6, "Brave New World", "Aldous Huxley", 1932),
        (7, "Wuthering Heights", "Emily Brontë", 1847),
    ]
    cursor.executemany(
        """
        INSERT OR REPLACE INTO books (id, title, author, year)
        VALUES (?, ?, ?, ?)
        """,
        books,
    )
    conn.commit()
