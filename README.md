# 🚀 DBAnu - The Ultimate FastAPI SQL Query Engine

**Transform your SQL queries into production-ready REST APIs in minutes, not hours.**

DBAnu is a revolutionary Python library that eliminates the boilerplate of creating database APIs. With just a few lines of code, you can expose any SQL query as a fully-featured FastAPI endpoint with built-in filtering, pagination, authentication, logging, and even multi-database union queries.

## ✨ Why DBAnu Matters

### The Problem: Database API Development is Repetitive

Building database APIs typically involves:
- Writing the same CRUD endpoints repeatedly
- Implementing pagination logic over and over
- Adding authentication checks to every endpoint
- Creating complex filtering systems
- Handling database connection management
- Writing extensive validation logic

### The Solution: DBAnu Automates the Boring Parts

DBAnu turns this:

```python
# Traditional approach - 50+ lines of boilerplate
@app.get("/api/books")
async def get_books(
    author: str = None, 
    min_year: int = None,
    limit: int = 100, 
    offset: int = 0
):
    # Validate inputs
    # Build dynamic WHERE clause
    # Handle pagination
    # Execute query
    # Format response
    # Handle errors
    # Add logging
    # Check authentication
    # ... and much more
```

Into this:

```python
# DBAnu approach - 3 lines of code
serve_select(
    app=app,
    query_engine=query_engine,
    path="/api/books",
    select_query="SELECT * FROM books LIMIT ? OFFSET ?"
)
```

## 🎯 Key Features That Make DBAnu Special

### 🚀 **Instant API Generation**
Turn any SQL query into a REST endpoint in seconds

### 🔄 **Multi-Database Union Queries**
Combine results from SQLite, PostgreSQL, MySQL in a single API call

### 🛡️ **Type-Safe Everything**
Pydantic-powered validation for filters, responses, and middleware

### 🔧 **Powerful Middleware System**
Intercept and modify queries, add logging, authentication, and more

### 📊 **Smart Pagination**
Built-in pagination with priority-based union pagination across databases

### 🔌 **Seamless FastAPI Integration**
Works with all FastAPI features - dependencies, background tasks, WebSockets

### 🎨 **Flexible Filtering**
Define complex filters with Pydantic models, automatically applied to your queries

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

## 📚 Usage Examples - From Simple to Complex

### Level 1: Basic Query Endpoint

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

### Level 2: Advanced Filtering

```python
from pydantic import BaseModel
from dbanu import serve_select, SQLiteQueryEngine

app = FastAPI()

# Define your filter model
class BookFilter(BaseModel):
    author: str | None = None
    min_year: int | None = None
    max_year: int | None = None

# Define your response model
class BookData(BaseModel):
    id: int
    title: str
    author: str
    year: int

query_engine = SQLiteQueryEngine()

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
        "AND (year <= ? OR ? IS NULL) "
        "LIMIT ? OFFSET ?"
    ),
    select_param=lambda filters, limit, offset: [
        filters.author, filters.author,
        filters.min_year, filters.min_year,
        filters.max_year, filters.max_year,
        limit, offset
    ],
    count_query=(
        "SELECT COUNT(*) FROM books "
        "WHERE (author = ? OR ? IS NULL) "
        "AND (year >= ? OR ? IS NULL) "
        "AND (year <= ? OR ? IS NULL)"
    ),
    count_param=lambda filters: [
        filters.author, filters.author,
        filters.min_year, filters.min_year,
        filters.max_year, filters.max_year
    ]
)
```

**Usage:**
```bash
# Get books by Stephen King published after 2000
GET /api/books?author=Stephen%20King&min_year=2000&limit=10&offset=0
```

### Level 3: Multi-Database Union Queries

**Query multiple databases simultaneously and get unified results!**

```python
from fastapi import FastAPI
from dbanu import serve_union, SelectSource, SQLiteQueryEngine, PostgreSQLQueryEngine, MySQLQueryEngine

app = FastAPI()

# Create engines for different databases
sqlite_engine = SQLiteQueryEngine(db_path="./classic_literature.db")
pgsql_engine = PostgreSQLQueryEngine(
    host="localhost", port=5432, database="fantasy_books", 
    user="user", password="password"
)
mysql_engine = MySQLQueryEngine(
    host="localhost", port=3306, database="scifi_books",
    user="user", password="password"
)

# Combine all databases in one endpoint
serve_union(
    app=app,
    sources={
        "classics": SelectSource(
            query_engine=sqlite_engine,
            select_query="SELECT *, 'classic' as genre FROM books LIMIT ? OFFSET ?",
            count_query="SELECT COUNT(*) FROM books"
        ),
        "fantasy": SelectSource(
            query_engine=pgsql_engine,
            select_query="SELECT *, 'fantasy' as genre FROM books LIMIT %s OFFSET %s",
            count_query="SELECT COUNT(*) FROM books"
        ),
        "scifi": SelectSource(
            query_engine=mysql_engine,
            select_query="SELECT *, 'scifi' as genre FROM books LIMIT %s OFFSET %s",
            count_query="SELECT COUNT(*) FROM books"
        ),
    },
    path="/api/all-books",
    description="Get books from all databases combined"
)
```

**Usage:**
```bash
# Get books from ALL databases in one call
GET /api/all-books?limit=20&offset=0

# Control source priority (fantasy books first, then scifi, then classics)
GET /api/all-books?limit=20&offset=0&priority=fantasy,scifi,classics
```

### Level 4: Enterprise-Grade with Middleware & Dependencies

```python
from fastapi import Depends, FastAPI, HTTPException
from dbanu import serve_select, SQLiteQueryEngine, QueryContext
import time

app = FastAPI()
query_engine = SQLiteQueryEngine()

# Authentication dependency
async def get_current_user():
    return {"user_id": 1, "username": "demo_user", "role": "admin"}

# Rate limiting dependency
async def rate_limit_check():
    return True

# Middleware: Logging
def logging_middleware(context: QueryContext, next_handler):
    user_info = context.dependency_results.get("get_current_user", {})
    username = user_info.get("username", "anonymous")
    print(f"📝 Request from {username}: {context.filters.model_dump()}")
    result = next_handler()
    print(f"📝 Response: {len(result.data)} items")
    return result

# Middleware: Timing
def timing_middleware(context: QueryContext, next_handler):
    start_time = time.time()
    result = next_handler()
    end_time = time.time()
    print(f"⏱️ Query took {end_time - start_time:.3f}s")
    return result

# Middleware: Authorization
def authorization_middleware(context: QueryContext, next_handler):
    current_user = context.dependency_results.get("get_current_user")
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Role-based access control
    if current_user.get("role") not in ["admin", "editor"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    return next_handler()

# Create the enterprise endpoint
serve_select(
    app=app,
    query_engine=query_engine,
    path="/api/secure/books",
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
    middlewares=[logging_middleware, authorization_middleware, timing_middleware]
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

## 🔧 Advanced Features

### Custom Middleware Examples

**Query Modification Middleware:**
```python
def query_modification_middleware(context: QueryContext, next_handler):
    # Add tenant filtering
    tenant_id = context.dependency_results.get("tenant_id")
    if tenant_id:
        context.select_query = context.select_query.replace(
            "WHERE", f"WHERE tenant_id = {tenant_id} AND"
        )
    return next_handler()
```

**Caching Middleware:**
```python
import redis
redis_client = redis.Redis()

def caching_middleware(context: QueryContext, next_handler):
    cache_key = f"query:{context.select_query}:{context.select_params}"
    cached = redis_client.get(cache_key)
    if cached:
        return cached
    
    result = next_handler()
    redis_client.setex(cache_key, 300, result)  # Cache for 5 minutes
    return result
```

**Data Transformation Middleware:**
```python
def data_transformation_middleware(context: QueryContext, next_handler):
    result = next_handler()
    # Transform data before returning
    for item in result.data:
        item["formatted_title"] = item["title"].title()
    return result
```

## 🎯 Real-World Use Cases

### E-commerce Platform
```python
# Combine product data from multiple sources
serve_union(
    app=app,
    sources={
        "main_products": SelectSource(...),  # Primary PostgreSQL
        "legacy_products": SelectSource(...),  # Legacy MySQL
        "external_products": SelectSource(...),  # External API via SQLite
    },
    path="/api/products"
)
```

### Multi-tenant SaaS Application
```python
# Automatic tenant isolation
serve_select(
    app=app,
    path="/api/customers",
    dependencies=[Depends(get_tenant_id)],
    middlewares=[tenant_isolation_middleware]
)
```

### Analytics Dashboard
```python
# Real-time data from multiple databases
serve_union(
    app=app,
    sources={
        "user_metrics": SelectSource(...),  # User database
        "sales_data": SelectSource(...),    # Sales database
        "web_analytics": SelectSource(...), # Analytics database
    },
    path="/api/dashboard/metrics"
)
```

## 🚀 Running the Complete Example

### Quick Demo with Docker

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

### Sample Data Distribution

- **SQLite**: Classic Literature (The Great Gatsby, 1984, etc.)
- **PostgreSQL**: Fantasy (Harry Potter, Game of Thrones, etc.)
- **MySQL**: Science Fiction (Dune, Foundation, Neuromancer, etc.)

## 🧪 Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest tests/ -v

# Run specific tests
pytest tests/test_union_logic.py -v
```

## 🔍 How Union Pagination Works

DBAnu uses **priority-based pagination** for union queries:

```python
# Sources with different record counts
sources = {
    "source-1": 3 records,  # ["s1-r1", "s1-r2", "s1-r3"]
    "source-2": 4 records,  # ["s2-r1", "s2-r2", "s2-r3", "s2-r4"]
    "source-3": 5 records,  # ["s3-r1", "s3-r2", "s3-r3", "s3-r4", "s3-r5"]
}

priority = ["source-1", "source-2", "source-3"]
limit = 5
offset = 3

# Result: ["s2-r1", "s2-r2", "s2-r3", "s2-r4", "s3-r1"]
```

**Explanation:**
- Offset 3 skips all 3 records from source-1
- Source-2 provides 4 records (all of them)
- Source-3 provides 1 record to reach the limit of 5

This ensures proper pagination across the combined dataset rather than getting 15 records (5 from each source).

## 📖 API Reference

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
- `summary`: Optional API endpoint summary
- `description`: Optional API endpoint description

### `serve_union` Parameters

- `app`: FastAPI application instance
- `sources`: Dictionary of `SelectSource` objects for each database
- `path`: API endpoint path (default: "/get")
- `filter_model`: Pydantic model for filtering (applies to all sources)
- `data_model`: Pydantic model for response data
- `dependencies`: List of FastAPI dependencies
- `middlewares`: List of middleware functions
- `summary`: Optional API endpoint summary
- `description`: Optional API endpoint description

## 📄 License

MIT