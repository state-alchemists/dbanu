import time
from typing import Callable

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel

from dbanu import (
    MySQLQueryEngine,
    PostgreSQLQueryEngine,
    SelectSource,
    SQLiteQueryEngine,
    serve_select,
    serve_union,
)
from example.config import (
    MYSQL_DATABASE,
    MYSQL_HOST,
    MYSQL_PASSWORD,
    MYSQL_PORT,
    MYSQL_USER,
    PG_SQL_DATABASE,
    PG_SQL_HOST,
    PG_SQL_PASSWORD,
    PG_SQL_PORT,
    PG_SQL_USER,
    SQLITE_DB_PATH,
)
from example.setup import setup_sqlite

setup_sqlite()

# 1. Simplest implementation
app = FastAPI()
sqlite_query_engine = SQLiteQueryEngine(db_path=SQLITE_DB_PATH)
serve_select(
    app=app,
    query_engine=sqlite_query_engine,
    path="/api/v1/sqlite/books",
    select_query="SELECT * FROM books LIMIT ? OFFSET ?",
    count_query="SELECT count(1) FROM books",
)

pgsql_query_engine = PostgreSQLQueryEngine(
    host=PG_SQL_HOST,
    port=PG_SQL_PORT,
    database=PG_SQL_DATABASE,
    user=PG_SQL_USER,
    password=PG_SQL_PASSWORD,
)
serve_select(
    app=app,
    query_engine=pgsql_query_engine,
    path="/api/v1/pgsql/books",
    select_query="SELECT * FROM books LIMIT %s OFFSET %s",
    count_query="SELECT count(1) FROM books",
)

mysql_query_engine = MySQLQueryEngine(
    host=MYSQL_HOST,
    port=MYSQL_PORT,
    database=MYSQL_DATABASE,
    user=MYSQL_USER,
    password=MYSQL_PASSWORD,
)
serve_select(
    app=app,
    query_engine=mysql_query_engine,
    path="/api/v1/mysql/books",
    select_query="SELECT * FROM books LIMIT %s OFFSET %s",
    count_query="SELECT count(1) FROM books",
)

serve_union(
    app=app,
    sources={
        "sqlite": SelectSource(
            query_engine=sqlite_query_engine,
            select_query="SELECT *, 'sqlite' as source FROM books LIMIT ? OFFSET ?",
            count_query="SELECT COUNT(1) FROM books",
        ),
        "psql": SelectSource(
            query_engine=pgsql_query_engine,
            select_query="SELECT *, 'psql' as source FROM books LIMIT %s OFFSET %s",
            count_query="SELECT COUNT(1) FROM books",
        ),
        "mysql": SelectSource(
            query_engine=mysql_query_engine,
            select_query="SELECT *, 'mysql' as source FROM books LIMIT %s OFFSET %s",
            count_query="SELECT COUNT(1) FROM books",
        ),
    },
    path="/api/v1/all/books",
    description="Get all books from sqlite, postgre, and mysql",
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
    query_engine=sqlite_query_engine,
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


def query(query_template: str) -> Callable[[FreeQueryFilter], str]:
    def create_query(filter: FreeQueryFilter) -> str:
        if filter.table == "":
            raise ValueError("Table name cannot be empty")
        return query_template.format(_table=filter.table, _filters=filter.condition)

    return create_query


serve_select(
    app=app,
    query_engine=sqlite_query_engine,
    path="/api/v1/query",
    filter_model=FreeQueryFilter,
    select_query=query("SELECT * FROM {_table} WHERE {_filters} LIMIT ? OFFSET ?"),
    count_query=query("SELECT count(1) FROM {_table} WHERE {_filters}"),
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
    query_engine=sqlite_query_engine,
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
    middlewares=[logging_middleware, authorization_middleware, timing_middleware],
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
