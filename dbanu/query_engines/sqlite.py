import sqlite3
from typing import Any

from dbanu.select_route import SelectEngine


class SQLiteQueryEngine(SelectEngine):
    """
    A real SQLite query engine that connects to an actual database.
    """

    def __init__(self, db_path: str = ":memory:"):
        self._db_path = db_path
        # Don't setup database here - do it on first connection

    def _setup_database(self, conn: sqlite3.Connection):
        """Override this"""

    def select(self, query: str, *params: Any) -> list[Any]:
        """
        Execute a SELECT query against the SQLite database.
        """
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()

        # Setup database if needed
        self._setup_database(conn)

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
            conn.close()

    def select_count(self, query: str, *params: Any) -> int:
        """
        Execute a COUNT query against the SQLite database.
        """
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()

        # Setup database if needed
        self._setup_database(conn)

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
            conn.close()
