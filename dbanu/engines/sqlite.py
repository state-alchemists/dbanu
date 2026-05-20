"""
SQLite query engine
"""

import sqlite3
import threading
from typing import Any

from dbanu.core.engine import SelectEngine


class SQLiteQueryEngine(SelectEngine):
    """
    A real SQLite query engine that connects to an actual database.

    A single shared connection is reused for the lifetime of the engine and
    guarded by a lock; SQLite connections are cheap to open but ``:memory:``
    databases vanish when the connection closes, so reuse is mandatory.
    """

    def __init__(self, db_path: str = ":memory:"):
        self._db_path = db_path
        self._connection: sqlite3.Connection | None = None
        self._connection_lock = threading.Lock()
        self._setup_done = False

    def _setup_database(self, conn: sqlite3.Connection):
        """Override this"""

    def _standardize_query(self, query: str) -> str:
        return query.replace("%s", "?")

    def _get_connection(self) -> sqlite3.Connection:
        # Lazy init so the engine can be constructed before the database
        # file is available, and so :memory: databases survive across calls.
        if self._connection is None:
            with self._connection_lock:
                if self._connection is None:
                    conn = sqlite3.connect(
                        self._db_path, check_same_thread=False
                    )
                    if not self._setup_done:
                        self._setup_database(conn)
                        self._setup_done = True
                    self._connection = conn
        return self._connection

    def select(self, query: str, *params: Any) -> list[Any]:
        """
        Execute a SELECT query against the SQLite database.
        """
        conn = self._get_connection()
        standardized_query = self._standardize_query(query)
        # SQLite cursors share connection state; serialize access.
        with self._connection_lock:
            cursor = conn.cursor()
            try:
                if params:
                    cursor.execute(standardized_query, params)
                else:
                    cursor.execute(standardized_query)
                results = cursor.fetchall()
                if results and len(results) > 0:
                    column_names = [description[0] for description in cursor.description]
                    return [dict(zip(column_names, row)) for row in results]
                return []
            finally:
                cursor.close()

    def select_count(self, query: str, *params: Any) -> int:
        """
        Execute a COUNT query against the SQLite database.
        """
        conn = self._get_connection()
        standardized_query = self._standardize_query(query)
        with self._connection_lock:
            cursor = conn.cursor()
            try:
                if params:
                    cursor.execute(standardized_query, params)
                else:
                    cursor.execute(standardized_query)
                result = cursor.fetchone()
                return result[0] if result else 0
            finally:
                cursor.close()

    def close(self) -> None:
        """Close the shared SQLite connection."""
        if self._connection is not None:
            try:
                self._connection.close()
            finally:
                self._connection = None
