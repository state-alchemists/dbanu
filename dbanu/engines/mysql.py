"""
MySQL query engine
"""

import threading
from typing import Any

import mysql.connector
from mysql.connector import pooling as mysql_pooling

from dbanu.core.engine import SelectEngine


class MySQLQueryEngine(SelectEngine):
    """
    A MySQL query engine that connects to a MySQL database.

    Uses mysql-connector's built-in connection pool so individual requests
    do not pay the cost of opening a fresh handshake on every call.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 3306,
        database: str = "mysql",
        user: str = "root",
        password: str = "",
        pool_size: int = 10,
        pool_name: str = "dbanu_mysql",
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
        # MySQL connector caps pool_size at 32; clamp here so an over-eager
        # caller does not crash at pool creation time.
        self._pool_size = max(1, min(pool_size, 32))
        self._pool_name = pool_name
        self._pool: mysql_pooling.MySQLConnectionPool | None = None
        self._pool_lock = threading.Lock()

    def _get_pool(self) -> mysql_pooling.MySQLConnectionPool:
        if self._pool is None:
            with self._pool_lock:
                if self._pool is None:
                    self._pool = mysql_pooling.MySQLConnectionPool(
                        pool_name=self._pool_name,
                        pool_size=self._pool_size,
                        pool_reset_session=True,
                        **self._connection_params,
                    )
        return self._pool

    def _get_connection(self):
        """Borrow a pooled connection."""
        return self._get_pool().get_connection()

    def select(self, query: str, *params: Any) -> list[Any]:
        """
        Execute a SELECT query against the MySQL database.
        """
        conn = self._get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            results = cursor.fetchall()
            return list(results) if results else []
        finally:
            cursor.close()
            # Returning a pooled connection just releases it back to the pool.
            conn.close()

    def select_count(self, query: str, *params: Any) -> int:
        """
        Execute a COUNT query against the MySQL database.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            result = cursor.fetchone()
            return result[0] if result else 0
        finally:
            cursor.close()
            conn.close()
