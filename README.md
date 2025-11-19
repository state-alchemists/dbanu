# 🚀 DBAnu - FastAPI SQL Query Engine

**Transform SQL queries into production-ready REST APIs in seconds.**

DBAnu eliminates the boilerplate of creating database APIs. With just a few lines of code, expose any SQL query as a fully-featured FastAPI endpoint with built-in filtering, pagination, authentication, and middleware support.

## ✨ Why DBAnu?

### The Problem
Building database APIs involves repetitive work:
- Writing the same CRUD endpoints
- Implementing pagination logic
- Adding authentication checks
- Creating filtering systems
- Handling database connections

### The Solution
DBAnu turns this:

```python
# Traditional approach - 50+ lines
@app.get("/api/books")
async def get_books(author: str = None, limit: int = 100, offset: int = 0):
    # Validate inputs, build WHERE clause, handle pagination...
    # ...and much more boilerplate
```

Into this:

```python
# DBAnu approach - 3 lines
serve_select(
    app=app,
    query_engine=query_engine,
    path="/api/books",
    select_query="SELECT * FROM books LIMIT ? OFFSET ?"
)
```

## 🎯 Key Features

### 🚀 **Instant API Generation**
Turn any SQL query into a REST endpoint in seconds

### 🔄 **Multi-Database Union Queries**
Combine results from SQLite, PostgreSQL, MySQL in a single API call

### 🛡️ **Type-Safe Everything**
Pydantic-powered validation for filters, responses, and middleware

### 🔧 **Powerful Middleware System**
Intercept and modify queries, add logging, authentication, and more. **Middleware functions must be async**.

### 🎛️ **Dynamic Query Generation**
Create queries on-the-fly based on request parameters

### 📊 **Smart Pagination**
Built-in pagination with priority-based union pagination across databases

## 🚀 Quick Start

### Installation

```bash
pip install dbanu
```

### From Zero to API in 60 Seconds

```python
from fastapi import FastAPI
from dbanu import serve_select, SQLiteQueryEngine

app = FastAPI()

# Create a SQLite query engine
query_engine = SQLiteQueryEngine()

# 🎉 Create your first API endpoint
serve_select(
    app=app,
    query_engine=query_engine,
    path="/api/books",
    select_query="SELECT id, title, author FROM books LIMIT ? OFFSET ?",
    count_query="SELECT COUNT(*) FROM books"
)
```

**That's it!** You now have a fully functional API with:
- ✅ Automatic pagination (`limit` and `offset` parameters)
- ✅ Total count for frontend pagination
- ✅ Proper error handling
- ✅ FastAPI documentation at `/docs`

## 📚 Usage Examples

### Basic Query Endpoint

```python
from fastapi import FastAPI
from dbanu import serve_select, SQLiteQueryEngine

app = FastAPI()
query_engine = SQLiteQueryEngine()

# Simple books endpoint
serve_select(
    app=app,
    query_engine=query_engine,
    path="/api/books",
    select_query="SELECT * FROM books LIMIT ? OFFSET ?",
    count_query="SELECT COUNT(*) FROM books"
)
```

**Usage:**
```bash
GET /api/books?limit=10&offset=0
```

### Advanced Filtering

```python
from pydantic import BaseModel
from dbanu import serve_select, SQLiteQueryEngine

app = FastAPI()

# Define your filter model
class BookFilter(BaseModel):
    author: str | None = None
    min_year: int | None = None

query_engine = SQLiteQueryEngine()

serve_select(
    app=app,
    query_engine=query_engine,
    path="/api/books",
    filter_model=BookFilter,
    select_query=(
        "SELECT id, title, author, year FROM books "
        "WHERE (author = %s OR %s IS NULL) "
        "AND (year >= %s OR %s IS NULL) "
        "LIMIT %s OFFSET %s"
    ),
    select_param=lambda filters, limit, offset: [
        filters.author, filters.author,
        filters.min_year, filters.min_year,
        limit, offset
    ]
)
```

**Usage:**
```bash
# Get books by Stephen King published after 2000
GET /api/books?author=Stephen%20King&min_year=2000&limit=10&offset=0
```

### Dynamic Queries

**Create queries dynamically based on filters:**

```python
from typing import Callable
from pydantic import BaseModel
from dbanu import serve_select, SQLiteQueryEngine

app = FastAPI()

class DynamicFilter(BaseModel):
    table: str
    condition: str = "1=1"

def create_query(query_template: str) -> Callable[[DynamicFilter], str]:
    def query_builder(filters: DynamicFilter) -> str:
        if filters.table == "":
            raise ValueError("Table name cannot be empty")
        return query_template.format(
            _table=filters.table, 
            _filters=filters.condition
        )
    return query_builder

query_engine = SQLiteQueryEngine()

serve_select(
    app=app,
    query_engine=query_engine,
    path="/api/dynamic",
    filter_model=DynamicFilter,
    select_query=create_query("SELECT * FROM {_table} WHERE {_filters} LIMIT %s OFFSET %s"),
    count_query=create_query("SELECT COUNT(*) FROM {_table} WHERE {_filters}")
)
```

**Usage:**
```bash
# Query books table with author filter
GET /api/dynamic?table=books&condition=author='Stephen%20King'&limit=10&offset=0
```

### Multi-Database Union Queries

**Query multiple databases simultaneously and get unified results!**

```python
from fastapi import FastAPI
from dbanu import serve_union, SelectSource, SQLiteQueryEngine, PostgreSQLQueryEngine

app = FastAPI()

# Create engines for different databases
sqlite_engine = SQLiteQueryEngine(db_path="./classic_literature.db")
pgsql_engine = PostgreSQLQueryEngine(
    host="localhost", database="fantasy_books", 
    user="user", password="password"
)

# Combine all databases in one endpoint
serve_union(
    app=app,
    sources={
        "classics": SelectSource(
            query_engine=sqlite_engine,
            select_query="SELECT *, 'classic' as genre FROM books LIMIT %s OFFSET %s",
            count_query="SELECT COUNT(*) FROM books"
        ),
        "fantasy": SelectSource(
            query_engine=pgsql_engine,
            select_query="SELECT *, 'fantasy' as genre FROM books LIMIT %s OFFSET %s",
            count_query="SELECT COUNT(*) FROM books"
        ),
    },
    path="/api/all-books",
    source_priority=["fantasy", "classics"]  # Default priority order
)
```

**Usage:**
```bash
# Get books from ALL databases in one call
GET /api/all-books?limit=20&offset=0

# Control source priority
GET /api/all-books?limit=20&offset=0&priority=fantasy,classics
```

### Enterprise-Grade with Middleware

```python
from fastapi import Depends, FastAPI, HTTPException
from dbanu import serve_select, SQLiteQueryEngine, QueryContext

app = FastAPI()
query_engine = SQLiteQueryEngine()

# Authentication dependency
async def get_current_user():
    return {"user_id": 1, "username": "demo_user", "role": "admin"}

# Middleware: Logging
# IMPORTANT: Middleware functions MUST be async
async def logging_middleware(context: QueryContext, next_handler):
    user_info = context.dependency_results.get("get_current_user", {})
    username = user_info.get("username", "anonymous")
    print(f"📝 Request from {username}: {context.filters.model_dump()}")
    return await next_handler(context)

# Middleware: Authorization
# IMPORTANT: Middleware functions MUST be async
async def authorization_middleware(context: QueryContext, next_handler):
    current_user = context.dependency_results.get("get_current_user")
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Role-based access control
    if current_user.get("role") not in ["admin", "editor"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    return await next_handler(context)

# Create the secure endpoint
serve_select(
    app=app,
    query_engine=query_engine,
    path="/api/secure/books",
    dependencies=[Depends(get_current_user)],
    middlewares=[logging_middleware, authorization_middleware],
    select_query="SELECT id, title, author FROM books LIMIT %s OFFSET %s"
)
```

## 🏗️ Database Engines

### SQLite
```python
from dbanu import SQLiteQueryEngine
query_engine = SQLiteQueryEngine(db_path="./database.db")
```

### PostgreSQL
```python
from dbanu import PostgreSQLQueryEngine
query_engine = PostgreSQLQueryEngine(
    host="localhost",
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
    database="mydb",
    user="user",
    password="password"
)
```

## 🚀 Running the Example

### Quick Demo

1. **Start the demo environment:**
```bash
cd example
docker-compose up -d
```

2. **Run the example server:**
```bash
python -m example.server
```

3. **Explore the APIs:**
   - Visit http://localhost:8000/docs
   - Test different endpoints:
     - `/api/v1/sqlite/books` - Classic literature
     - `/api/v1/pgsql/books` - Fantasy books  
     - `/api/v1/mysql/books` - Science fiction
     - `/api/v1/all/books` - **All books combined!**

## 🧪 Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest tests/ -v
```

## 📖 API Reference

### `serve_select` Parameters

- `app`: FastAPI application instance
- `query_engine`: Database query engine (SQLite, PostgreSQL, or MySQL)
- `select_query`: SQL SELECT query string or callable function that receives filters
- `select_param`: Function to generate query parameters from filters
- `count_query`: Optional SQL COUNT query for pagination (string or callable function)
- `path`: API endpoint path (default: "/get")
- `filter_model`: Pydantic model for filtering
- `data_model`: Pydantic model for response data
- `dependencies`: List of FastAPI dependencies
- `middlewares`: List of middleware functions that receive `QueryContext` (**MUST be async functions**)

### `serve_union` Parameters

- `app`: FastAPI application instance
- `sources`: Dictionary of `SelectSource` objects for each database
- `path`: API endpoint path (default: "/get")
- `filter_model`: Pydantic model for filtering (applies to all sources)
- `data_model`: Pydantic model for response data
- `dependencies`: List of FastAPI dependencies
- `middlewares`: List of middleware functions (**MUST be async functions**)
- `source_priority`: List of source names for default priority ordering

## 📄 License

MIT