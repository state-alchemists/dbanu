# DBAnu - FastAPI SQL Query Engine

DBAnu is a lightweight Python library that simplifies creating FastAPI endpoints for SQL queries. It provides a clean, type-safe interface for exposing database queries as RESTful APIs with built-in support for filtering, pagination, dependency injection, and middleware.

## Features

- **Type-Safe Query Generation**: Automatically generate FastAPI routes from SQL queries
- **Flexible Filtering**: Support for complex filtering with Pydantic models
- **Built-in Pagination**: Automatic limit/offset pagination support
- **FastAPI Integration**: Seamless integration with FastAPI dependencies and middleware
- **Multiple Database Support**: SQLite, PostgreSQL, MySQL, and custom engines
- **Dependency Injection**: Access FastAPI dependencies in middleware
- **Middleware System**: Custom middleware for logging, authentication, authorization, and more

## Installation

```bash
pip install dbanu
```

## Quick Start

### Basic Usage

Create a simple FastAPI endpoint with SQLite:

```python
from fastapi import FastAPI
from dbanu import serve_select, SQLiteQueryEngine

app = FastAPI()

# Create a SQLite query engine
query_engine = SQLiteQueryEngine()

# Register a simple endpoint
serve_select(
    app=app,
    query_engine=query_engine,
    path="/api/books",
    select_query="SELECT id, title, author FROM books LIMIT ? OFFSET ?",
    select_param=lambda filters, limit, offset: [limit, offset]
)
```

### Advanced Usage with Filtering

```python
from pydantic import BaseModel
from fastapi import FastAPI
from dbanu import serve_select, SQLiteQueryEngine

app = FastAPI()

# Define filter model
class BookFilter(BaseModel):
    author: str | None = None
    min_year: int | None = None

# Define data model
class BookData(BaseModel):
    id: int
    title: str
    author: str
    year: int

# Create query engine
query_engine = SQLiteQueryEngine()

# Register endpoint with filtering
serve_select(
    app=app,
    query_engine=query_engine,
    path="/api/books",
    filter_model=BookFilter,
    data_model=BookData,
    select_query=(
        "SELECT id, title, author, year FROM books "
        "WHERE (author = ? OR ? IS NULL) "
        "AND (year >= ? OR ? IS NULL) "
        "LIMIT ? OFFSET ?"
    ),
    select_param=lambda filters, limit, offset: [
        filters.author, filters.author,
        filters.min_year, filters.min_year,
        limit, offset
    ],
    count_query=(
        "SELECT COUNT(*) FROM books "
        "WHERE (author = ? OR ? IS NULL) "
        "AND (year >= ? OR ? IS NULL)"
    ),
    count_param=lambda filters: [
        filters.author, filters.author,
        filters.min_year, filters.min_year
    ]
)
```

### Full Example with Dependencies and Middleware

```python
import sqlite3
from typing import Any
from pydantic import BaseModel
from fastapi import FastAPI, Depends
from dbanu import serve_select, SQLiteQueryEngine

app = FastAPI()

# Custom query engine with setup
class MyQueryEngine(SQLiteQueryEngine):
    def _setup_database(self, conn: sqlite3.Connection):
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                year INTEGER NOT NULL
            )
        """)
        books = [
            (1, "The Great Gatsby", "F. Scott Fitzgerald", 1925),
            (2, "To Kill a Mockingbird", "Harper Lee", 1960),
        ]
        cursor.executemany("INSERT OR REPLACE INTO books VALUES (?, ?, ?, ?)", books)
        conn.commit()

# FastAPI dependencies
async def get_current_user():
    return {"user_id": 1, "username": "demo_user"}

async def rate_limit_check():
    return True

# Middleware functions
def logging_middleware(filters: BaseModel, limit: int, offset: int, dependency_results: dict[str, Any], next_handler):
    user_info = dependency_results.get('get_current_user', {})
    username = user_info.get('username', 'anonymous')
    print(f"[LOG] Request from {username}: filters={filters.model_dump()}")
    result = next_handler()
    print(f"[LOG] Response: {len(result.data)} items")
    return result

def authorization_middleware(filters: BaseModel, limit: int, offset: int, dependency_results: dict[str, Any], next_handler):
    from fastapi import HTTPException
    
    current_user = dependency_results.get('get_current_user')
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    if current_user.get('user_id') != 1:
        raise HTTPException(status_code=403, detail="Access forbidden")
    
    return next_handler()

# Pydantic models
class BookFilter(BaseModel):
    author: str | None = None
    min_year: int | None = None

class BookData(BaseModel):
    id: int
    title: str
    author: str
    year: int

# Create query engine
query_engine = MyQueryEngine()

# Register endpoint with all features
serve_select(
    app=app,
    query_engine=query_engine,
    path="/api/v1/books",
    filter_model=BookFilter,
    data_model=BookData,
    select_query=(
        "SELECT id, title, author, year FROM books "
        "WHERE (author = ? OR ? IS NULL) "
        "AND (year >= ? OR ? IS NULL) "
        "LIMIT ? OFFSET ?"
    ),
    select_param=lambda filters, limit, offset: [
        filters.author, filters.author,
        filters.min_year, filters.min_year,
        limit, offset
    ],
    count_query=(
        "SELECT COUNT(*) FROM books "
        "WHERE (author = ? OR ? IS NULL) "
        "AND (year >= ? OR ? IS NULL)"
    ),
    count_param=lambda filters: [
        filters.author, filters.author,
        filters.min_year, filters.min_year
    ],
    dependencies=[Depends(get_current_user), Depends(rate_limit_check)],
    middlewares=[logging_middleware, authorization_middleware]
)

@app.get("/")
def read_root():
    return {"message": "DBAnu Books API is running!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Even More Complex Example

No, no such thing. If you really need something more complex, you probably need to actually code your own router.

## Database Engines

### SQLite

```python
from dbanu import SQLiteQueryEngine

query_engine = SQLiteQueryEngine()
```

### PostgreSQL

```python
from dbanu import PostgreSQLQueryEngine

query_engine = PostgreSQLQueryEngine(
    host="localhost",
    port=5432,
    database="mydb",
    user="user",
    password="password"
)
```

### MySQL

```python
from dbanu import MySQLQueryEngine

query_engine = MySQLQueryEngine(
    host="localhost",
    port=3306,
    database="mydb",
    user="user",
    password="password"
)
```

## API Reference

### `serve_select` Parameters

- `app`: FastAPI application instance
- `query_engine`: Database query engine (SQLite, PostgreSQL, or MySQL)
- `select_query`: SQL SELECT query string
- `select_param`: Function to generate query parameters from filters
- `count_query`: Optional SQL COUNT query for pagination
- `count_param`: Function to generate COUNT query parameters
- `path`: API endpoint path (default: "/get")
- `filter_model`: Pydantic model for filtering
- `data_model`: Pydantic model for response data
- `dependencies`: List of FastAPI dependencies
- `middlewares`: List of middleware functions

### Middleware Signature

Middleware functions should have the following signature:

```python
def middleware_name(
    filters: BaseModel,
    limit: int,
    offset: int,
    dependency_results: dict[str, Any],
    next_handler: Callable
) -> Any:
    # Your middleware logic
    return next_handler()
```

## Running the Example

```bash
python -m example.server
```

Visit http://localhost:8000/api/v1/books to test the API.

## License

MIT