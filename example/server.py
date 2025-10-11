import sqlite3
from typing import Any
from pydantic import BaseModel
from fastapi import FastAPI, Depends
from dbanu import serve_select, SQLiteQueryEngine

# Create FastAPI app
app = FastAPI()


# Define query engine with pre-seed data
class MyQueryEngine(SQLiteQueryEngine):
    def _setup_database(self, conn: sqlite3.Connection):
        """Set up the database with sample book data"""
        cursor = conn.cursor()
        # Create books table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                year INTEGER NOT NULL
            )
        """)
        # Insert sample data
        books = [
            (1, "The Great Gatsby", "F. Scott Fitzgerald", 1925),
            (2, "To Kill a Mockingbird", "Harper Lee", 1960),
            (3, "1984", "George Orwell", 1949),
            (4, "Pride and Prejudice", "Jane Austen", 1813),
            (5, "The Catcher in the Rye", "J.D. Salinger", 1951),
        ]
        cursor.executemany("""
            INSERT OR REPLACE INTO books (id, title, author, year)
            VALUES (?, ?, ?, ?)
        """, books)
        conn.commit()


# Example FastAPI dependencies
async def get_current_user():
    """Example dependency for authentication"""
    return {"user_id": 1, "username": "demo_user"}


async def rate_limit_check():
    """Example dependency for rate limiting"""
    return True


# Example middlewares
def logging_middleware(filters: BaseModel, limit: int, offset: int, dependency_results: dict[str, Any], next_handler):
    """Middleware for logging requests"""
    user_info = dependency_results.get('get_current_user', {})
    username = user_info.get('username', 'anonymous')
    print(f"[LOG] Request from {username}: filters={filters.model_dump()}, limit={limit}, offset={offset}")
    result = next_handler()
    print(f"[LOG] Response: {len(result.data)} items")
    return result


def timing_middleware(filters: BaseModel, limit: int, offset: int, dependency_results: dict[str, Any], next_handler):
    """Middleware for timing requests"""
    import time
    start_time = time.time()
    result = next_handler()
    end_time = time.time()
    print(f"[TIMING] Request took {end_time - start_time:.3f} seconds")
    return result


def authorization_middleware(filters: BaseModel, limit: int, offset: int, dependency_results: dict[str, Any], next_handler):
    """Middleware for authorization checks"""
    from fastapi import HTTPException
    
    # Access the current user from dependency results
    current_user = dependency_results.get('get_current_user')
    print(f"[CURRENT_USER] {current_user}")
    
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Example authorization check: only allow user_id 1 to access
    if current_user.get('user_id') != 1:
        raise HTTPException(status_code=403, detail="Access forbidden")
    
    # Check rate limiting
    rate_limit_passed = dependency_results.get('rate_limit_check', False)
    if not rate_limit_passed:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    # If all checks pass, proceed with the request
    return next_handler()


# Define Pydantic models for our book data
class BookFilter(BaseModel):
    """Filter model for book queries"""
    author: str | None = None
    min_year: int | None = None
    max_year: int | None = None


class BookData(BaseModel):
    """Data model for book records"""
    id: int
    title: str
    author: str
    year: int


# Create SQLite query engine instance
query_engine = MyQueryEngine()

# Register the books endpoint using serve_select with dependencies and middlewares
serve_select(
    app=app,
    query_engine=query_engine,
    path="/api/v1/books",
    filter_model=BookFilter,
    data_model=BookData,
    select_query=(
        "SELECT id, title, author, year FROM books "
        "WHERE (author = ? OR ? IS NULL) "
        "AND (year > ? OR ? IS NULL) "
        "AND (year < ? OR ? IS NULL) "
        "LIMIT ? OFFSET ?"
    ),
    select_param=lambda filters, limit, offset: [
        filters.author, filters.author, filters.min_year, filters.min_year, filters.max_year, filters.max_year, limit, offset
    ],
    count_query=(
        "SELECT COUNT(*) FROM books "
        "WHERE (author = ? OR ? IS NULL) "
        "AND (year > ? OR ? IS NULL) "
        "AND (year < ? OR ? IS NULL) "
    ),
    count_param=lambda filters: [
        filters.author, filters.author, filters.min_year, filters.min_year, filters.max_year, filters.max_year
    ],
    dependencies=[Depends(get_current_user), Depends(rate_limit_check)],
    middlewares=[logging_middleware, timing_middleware, authorization_middleware]
)


# Add a simple root endpoint
@app.get("/")
def read_root():
    return {"message": "DBAnu Books API is running! Visit /api/v1/books to see books data."}


if __name__ == "__main__":
    import uvicorn
    print("Starting DBAnu Books API...")
    print("Visit http://localhost:8000/api/v1/books to see the books endpoint")
    print("Try these examples:")
    print("  - http://localhost:8000/api/v1/books")
    print("  - http://localhost:8000/api/v1/books?author=George%20Orwell")
    print("  - http://localhost:8000/api/v1/books?min_year=1950")
    uvicorn.run(app, host="0.0.0.0", port=8000)