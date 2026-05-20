"""
PostgreSQL query engine
"""

import threading
from typing import Any

import psycopg2
from psycopg2 import pool as psycopg2_pool

from dbanu.core.engine import SelectEngine


class PostgreSQLQueryEngine(SelectEngine):
    """
    A PostgreSQL query engine that connects to a PostgreSQL database.

    Uses a thread-safe connection pool so individual requests do not pay
    the cost of opening a fresh TCP/TLS/auth handshake on every call.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "postgres",
        user: str = "postgres",
        password: str = "",
        min_connections: int = 1,
        max_connections: int = 10,
    ):
        self._host = host
        self._port = port
        self._database = database
        self._user = user
        self._password = password
        self._connection_params = {
            "host": host,
            "port": port,
            "database": database,
            "user": user,
            "password": password,
        }
        self._min_connections = min_connections
        self._max_connections = max_connections
        self._pool: psycopg2_pool.ThreadedConnectionPool | None = None
        self._pool_lock = threading.Lock()

    def _get_pool(self) -> psycopg2_pool.ThreadedConnectionPool:
        # Lazy init so the engine can be constructed before the database
        # is reachable (e.g. during application startup ordering).
        if self._pool is None:
            with self._pool_lock:
                if self._pool is None:
                    self._pool = psycopg2_pool.ThreadedConnectionPool(
                        self._min_connections,
                        self._max_connections,
                        **self._connection_params,
                    )
        return self._pool

    def _get_connection(self):
        """Borrow a connection from the pool."""
        return self._get_pool().getconn()

    def _put_connection(self, conn, *, discard: bool = False):
        """Return a connection to the pool, optionally discarding it."""
        pool = self._pool
        if pool is None:
            return
        try:
            pool.putconn(conn, close=discard)
        except psycopg2_pool.PoolError:
            # Pool is full or closed; drop the connection on the floor.
            try:
                conn.close()
            except Exception:
                pass

    def select(self, query: str, *params: Any) -> list[Any]:
        """
        Execute a SELECT query against the PostgreSQL database.
        """
        conn = self._get_connection()
        discard = False
        try:
            with conn.cursor() as cursor:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                results = cursor.fetchall()
                if results and len(results) > 0:
                    column_names = [description[0] for description in cursor.description]
                    return [dict(zip(column_names, row)) for row in results]
                return []
        except Exception:
            discard = True
            raise
        finally:
            self._put_connection(conn, discard=discard)

    def select_count(self, query: str, *params: Any) -> int:
        """
        Execute a COUNT query against the PostgreSQL database.
        """
        conn = self._get_connection()
        discard = False
        try:
            with conn.cursor() as cursor:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                result = cursor.fetchone()
                return result[0] if result else 0
        except Exception:
            discard = True
            raise
        finally:
            self._put_connection(conn, discard=discard)

    def close(self) -> None:
        """Close all pooled connections. Safe to call multiple times."""
        if self._pool is not None:
            try:
                self._pool.closeall()
            finally:
                self._pool = None
