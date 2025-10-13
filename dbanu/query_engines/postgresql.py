from typing import Any

import psycopg2

from dbanu.select_route import SelectEngine


class PostgreSQLQueryEngine(SelectEngine):
    """
    A PostgreSQL query engine that connects to a PostgreSQL database.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "postgres",
        user: str = "postgres",
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
        """Get a connection to the PostgreSQL database."""
        return psycopg2.connect(**self._connection_params)

    def select(self, query: str, *params: Any) -> list[Any]:
        """
        Execute a SELECT query against the PostgreSQL database.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Execute the query with parameters
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            # Fetch results
            results = cursor.fetchall()

            # Convert to list of dictionaries for Pydantic compatibility
            if results and len(results) > 0:
                # Get column names
                column_names = [description[0] for description in cursor.description]
                # Convert each row to a dictionary
                dict_results = []
                for row in results:
                    dict_results.append(dict(zip(column_names, row)))
                return dict_results
            else:
                return []

        except Exception as e:
            print(f"Query execution error: {e}")
            return []
        finally:
            cursor.close()
            conn.close()

    def select_count(self, query: str, *params: Any) -> int:
        """
        Execute a COUNT query against the PostgreSQL database.
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
