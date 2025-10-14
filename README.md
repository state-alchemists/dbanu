# DBAnu - FastAPI SQL Query Engine

DBAnu is a lightweight Python library that simplifies creating FastAPI endpoints for SQL queries. It provides a clean, type-safe interface for exposing database queries as RESTful APIs with built-in support for filtering, pagination, dependency injection, and middleware.

## Features

- **Type-Safe Query Generation**: Automatically generate FastAPI routes from SQL queries
- **Flexible Filtering**: Support for complex filtering with Pydantic models
- **Built-in Pagination**: Automatic limit/offset pagination support
- **FastAPI Integration**: Seamless integration with FastAPI dependencies and middleware
- **Multiple Database Support**: SQLite, PostgreSQL, MySQL, and custom engines
- **Dependency Injection**: Access FastAPI dependencies in middleware
- **Middleware System**: Powerful middleware system with `QueryContext` for intercepting and modifying queries, logging, authentication, authorization, and more

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
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from dbanu import SQLiteQueryEngine, QueryContext, serve_select

app = FastAPI()
query_engine = SQLiteQueryEngine()

# Define models
class BookFilter(BaseModel):
    author: str | None = None
    min_year: int | None = None

class BookData(BaseModel):
    id: int
    title: str
    author: str
    year: int

# Example dependencies
async def get_current_user():
    return {"user_id": 1, "username": "demo_user"}

# Example middlewares
def logging_middleware(context: QueryContext, next_handler):
    user_info = context.dependency_results.get("get_current_user", {})
    username = user_info.get("username", "anonymous")
    print(f"Request from {username}: filters={context.filters.model_dump()}")
    result = next_handler()
    print(f"Response: {len(result.data)} items")
    return result

def authorization_middleware(context: QueryContext, next_handler):
    current_user = context.dependency_results.get("get_current_user")
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return next_handler()

# Register endpoint with dependencies and middleware
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
    ],
    dependencies=[Depends(get_current_user)],
    middlewares=[logging_middleware, authorization_middleware]
)
```

For a complete example with more advanced middleware usage, please see `example/server.py`.

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
- `middlewares`: List of middleware functions that receive `QueryContext`

### Middleware System

DBAnu provides a powerful middleware system that allows you to intercept and modify queries, add logging, implement authentication, and more. Middleware functions receive a `QueryContext` object containing all query-related data and a `next_handler` callable to continue the middleware chain.

#### Middleware Signature

```python
from dbanu import QueryContext

def middleware_name(context: QueryContext, next_handler: Callable) -> Any:
    # Your middleware logic
    return next_handler()
```

#### QueryContext Object

The `QueryContext` contains all the data available to middleware:

```python
class QueryContext(BaseModel):
    select_query: str           # The SELECT query string
    select_params: list[Any]    # Parameters for SELECT query
    count_query: Optional[str]  # The COUNT query string (optional)
    count_params: list[Any]     # Parameters for COUNT query
    filters: BaseModel          # Filter model instance
    limit: int                  # Pagination limit
    offset: int                 # Pagination offset
    dependency_results: dict[str, Any]  # Results from FastAPI dependencies
```

#### Example Middleware Implementations

**Logging Middleware:**
```python
def logging_middleware(context: QueryContext, next_handler):
    user_info = context.dependency_results.get("get_current_user", {})
    username = user_info.get("username", "anonymous")
    print(f"Request from {username}: filters={context.filters.model_dump()}")
    print(f"Select query: {context.select_query}")
    print(f"Select params: {context.select_params}")
    result = next_handler()
    print(f"Response: {len(result.data)} items")
    return result
```

**Authorization Middleware:**
```python
def authorization_middleware(context: QueryContext, next_handler):
    current_user = context.dependency_results.get("get_current_user")
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    # Add custom authorization logic here
    return next_handler()
```

**Query Modification Middleware:**
```python
def query_modification_middleware(context: QueryContext, next_handler):
    # Modify the query or parameters
    context.select_query = context.select_query.replace("__table__", "books")
    context.select_params = [context.limit, context.offset]
    return next_handler()
```

## Running the Example

```bash
python -m example.server
```

Visit http://localhost:8000/docs to test the API.

## License

MIT
