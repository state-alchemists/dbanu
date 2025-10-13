from typing import Any

import mysql.connector

from dbanu.select_route import SelectEngine


class MySQLQueryEngine(SelectEngine):
    """
    A MySQL query engine that connects to a MySQL database.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 3306,
        database: str = "mysql",
        user: str = "root",
        password: str = "",
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

    def _get_connection(self):
        """Get a connection to the MySQL database."""
        return mysql.connector.connect(**self._connection_params)

    def select(self, query: str, *params: Any) -> list[Any]:
        """
        Execute a SELECT query against the MySQL database.
        """
        conn = self._get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            # Execute the query with parameters
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            # Fetch results (MySQL connector with dictionary=True returns dicts)
            results = cursor.fetchall()

            # Convert to list of dictionaries for Pydantic compatibility
            # MySQL connector with dictionary=True already returns dicts
            return list(results) if results else []

        except Exception as e:
            print(f"Query execution error: {e}")
            return []
        finally:
            cursor.close()
            conn.close()

    def select_count(self, query: str, *params: Any) -> int:
        """
        Execute a COUNT query against the MySQL database.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Execute the query with parameters
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            # Fetch the count result
            result = cursor.fetchone()
            return result[0] if result else 0

        except Exception as e:
            print(f"Count query execution error: {e}")
            return 0
        finally:
            cursor.close()
            conn.close()
