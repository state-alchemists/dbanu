"""
DBAnu - FastAPI SQL Query Engine

A lightweight Python library that simplifies creating FastAPI endpoints for SQL queries.
"""

from dbanu.api import SelectSource, serve_select, serve_union
from dbanu.core import QueryContext
from dbanu.engines import MySQLQueryEngine, PostgreSQLQueryEngine, SQLiteQueryEngine

__all__ = [
    "MySQLQueryEngine",
    "PostgreSQLQueryEngine",
    "SQLiteQueryEngine",
    "QueryContext",
    "SelectSource",
    "serve_select",
    "serve_union",
]

# Assert all exports for backward compatibility
assert MySQLQueryEngine
assert PostgreSQLQueryEngine
assert QueryContext
assert SQLiteQueryEngine
assert SelectSource
assert serve_select
assert serve_union
