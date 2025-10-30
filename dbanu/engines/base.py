"""
Base engine class with common functionality
"""

from abc import ABC
from typing import Any

from dbanu.core.engine import SelectEngine


class BaseQueryEngine(SelectEngine, ABC):
    """Base class for query engines with common error handling"""

    def _handle_query_error(self, error: Exception, query_type: str) -> Any:
        """Handle query execution errors consistently"""
        print(f"{query_type} query execution error: {error}")
        if query_type == "COUNT":
            return 0
        return []
