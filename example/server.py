import sqlite3
import time
from typing import Any
from pydantic import BaseModel
from fastapi import FastAPI, Depends, HTTPException
from dbanu import serve_select, SQLiteQueryEngine

# Prepare in memory DB
class CustomQueryEngine(SQLiteQueryEngine):
    def _setup_database(self, conn: sqlite3.Connection):

        conn = sqlite3.connect(":memory:")
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

# Create FastAPI app

# 1. Simplest implementation
app = FastAPI()
query_engine = CustomQueryEngine()

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
)

# 3. Custom Table and Filter

class FreeSQLiteQueryEngine(CustomQueryEngine):
    def _mutate_query(self, query: str, params: Any) -> tuple[str, list[Any]]:
        new_params = list(params)
        table_name = new_params.pop(0).strip()
        if table_name == "":
            raise ValueError("Table name cannot be empty")
        filters = new_params.pop(0).strip()
        if filters == "":
            filters = "1=1"
        new_query = query.replace("__table__", table_name).replace("__filters__", filters)
        print(new_query, new_params)
        return new_query, new_params

    def select(self, query: str, *params: Any) -> list[Any]:
        new_query, new_params = self._mutate_query(query, params) 
        return super().select(new_query, *new_params)

    def select_count(self, query: str, *params: Any) -> int:
        new_query, new_params = self._mutate_query(query, params) 
        return super().select_count(new_query, *new_params)


class FreeQueryFilter(BaseModel):
    table: str
    condition: str


serve_select(
    app=app,
    query_engine=FreeSQLiteQueryEngine(),
    path="/api/v1/query",
    filter_model=FreeQueryFilter,
    select_query="SELECT * FROM __table__ WHERE __filters__ LIMIT ? OFFSET ?",
    select_param=lambda filters, limit, offset: [
        filters.table, filters.condition, limit, offset
    ],
    count_query="SELECT count(1) FROM __table__ WHERE __filters__",
    count_param=lambda filters: [filters.table, filters.condition],
)



# 4. Register the books endpoint with filters, dependencies and middlewares

## Example FastAPI dependencies
async def get_current_user():
    """Example dependency for authentication"""
    return {"user_id": 1, "username": "demo_user"}


async def rate_limit_check():
    """Example dependency for rate limiting"""
    return True


## Example middlewares
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
    start_time = time.time()
    result = next_handler()
    end_time = time.time()
    print(f"[TIMING] Request took {end_time - start_time:.3f} seconds")
    return result


def authorization_middleware(filters: BaseModel, limit: int, offset: int, dependency_results: dict[str, Any], next_handler):
    """Middleware for authorization checks"""
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
    return {
        "message": 'DBAnu Books API is running! Visit <a href="/docs">/docs</a> to see the API specs.'
    }


if __name__ == "__main__":
    import uvicorn
    print("Starting DBAnu Books API...")
    uvicorn.run(app, host="0.0.0.0", port=8000)