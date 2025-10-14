import os
import sqlite3
import time
from typing import Any

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel

from dbanu import SQLiteQueryEngine, QueryContext, serve_select

CURRENT_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(CURRENT_DIR, "sample.db")
conn = sqlite3.connect(DB_PATH)
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
# Insert sample data
books = [
    (1, "The Great Gatsby", "F. Scott Fitzgerald", 1925),
    (2, "To Kill a Mockingbird", "Harper Lee", 1960),
    (3, "1984", "George Orwell", 1949),
    (4, "Pride and Prejudice", "Jane Austen", 1813),
    (5, "The Catcher in the Rye", "J.D. Salinger", 1951),
]
cursor.executemany(
    """
    INSERT OR REPLACE INTO books (id, title, author, year)
    VALUES (?, ?, ?, ?)
    """,
    books,
)
conn.commit()


# 1. Simplest implementation
app = FastAPI()
query_engine = SQLiteQueryEngine(db_path=DB_PATH)

serve_select(
    app=app,
    query_engine=query_engine,
    path="/api/v1/books",
    select_query="SELECT * FROM books LIMIT ? OFFSET ?",
    count_query="SELECT count(1) FROM books",
)


# 2. Register the books endpoint with filters


## Define Pydantic models for our book data
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


serve_select(
    app=app,
    query_engine=query_engine,
    path="/api/v2/books",
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
        filters.author,
        filters.author,
        filters.min_year,
        filters.min_year,
        filters.max_year,
        filters.max_year,
        limit,
        offset,
    ],
    count_query=(
        "SELECT COUNT(*) FROM books "
        "WHERE (author = ? OR ? IS NULL) "
        "AND (year > ? OR ? IS NULL) "
        "AND (year < ? OR ? IS NULL) "
    ),
    count_param=lambda filters: [
        filters.author,
        filters.author,
        filters.min_year,
        filters.min_year,
        filters.max_year,
        filters.max_year,
    ],
)

# 3. Custom Table and Filter

class FreeQueryFilter(BaseModel):
    table: str
    condition: str


def modify_query(context: QueryContext, next_handler):
    context.count_params = []
    context.select_params = []
    table_name = context.filters.table.strip()
    if table_name == "":
        raise ValueError("Table name cannot be empty")
    condition = context.filters.condition.strip()
    if condition == "":
        condition = "1=1"
    context.select_query = _construct_query(
        context.select_query, table_name, condition
    )
    context.select_params = [context.limit, context.offset]
    if context.count_query is not None:
        context.count_query = _construct_query(
            context.count_query, table_name, condition
        )
    print(context)
    return next_handler()


def _construct_query(query: str, table_name: str, condition: str) -> str:
    return query.replace("__table__", table_name).replace("__filters__", condition)


serve_select(
    app=app,
    query_engine=query_engine,
    path="/api/v1/query",
    filter_model=FreeQueryFilter,
    select_query="SELECT * FROM __table__ WHERE __filters__ LIMIT ? OFFSET ?",
    count_query="SELECT count(1) FROM __table__ WHERE __filters__",
    middlewares=[modify_query]
)


# 4. Register the books endpoint with filters, dependencies and middlewares


## Example FastAPI dependencies
async def get_current_user():
    """Example dependency for authentication"""
    return {"user_id": 1, "username": "demo_user"}


async def rate_limit_check():
    """Example dependency for rate limiting"""
    return True


## Example middlewares with new Context-based signature
def logging_middleware(context, next_handler):
    """Middleware for logging requests"""
    user_info = context.dependency_results.get("get_current_user", {})
    username = user_info.get("username", "anonymous")
    print(
        f"[LOG] Request from {username}: filters={context.filters.model_dump()}, limit={context.limit}, offset={context.offset}"
    )
    print(f"[LOG] Select query: {context.select_query}")
    print(f"[LOG] Select params: {context.select_params}")
    result = next_handler()
    print(f"[LOG] Response: {len(result.data)} items")
    return result


def timing_middleware(context, next_handler):
    """Middleware for timing requests"""
    start_time = time.time()
    result = next_handler()
    end_time = time.time()
    print(f"[TIMING] Request took {end_time - start_time:.3f} seconds")
    return result


def authorization_middleware(context, next_handler):
    """Middleware for authorization checks"""
    # Access the current user from dependency results
    current_user = context.dependency_results.get("get_current_user")
    print(f"[CURRENT_USER] {current_user}")
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    # Example authorization check: only allow user_id 1 to access
    if current_user.get("user_id") != 1:
        raise HTTPException(status_code=403, detail="Access forbidden")
    # Check rate limiting
    rate_limit_passed = context.dependency_results.get("rate_limit_check", False)
    if not rate_limit_passed:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    # If all checks pass, proceed with the request
    return next_handler()


serve_select(
    app=app,
    query_engine=query_engine,
    path="/api/v3/books",
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
        filters.author,
        filters.author,
        filters.min_year,
        filters.min_year,
        filters.max_year,
        filters.max_year,
        limit,
        offset,
    ],
    count_query=(
        "SELECT COUNT(*) FROM books "
        "WHERE (author = ? OR ? IS NULL) "
        "AND (year > ? OR ? IS NULL) "
        "AND (year < ? OR ? IS NULL) "
    ),
    count_param=lambda filters: [
        filters.author,
        filters.author,
        filters.min_year,
        filters.min_year,
        filters.max_year,
        filters.max_year,
    ],
    dependencies=[Depends(get_current_user), Depends(rate_limit_check)],
    middlewares=[
        logging_middleware, 
        authorization_middleware, 
        timing_middleware
    ],
)


# Add a simple root endpoint
@app.get("/")
def read_root():
    return {
        "message": 'DBAnu Books API is running! Visit <a href="/docs">/docs</a> to see the API specs.'
    }


if __name__ == "__main__":
    import uvicorn

    print("Starting DBAnu Books API...")
    uvicorn.run(app, host="0.0.0.0", port=8000)