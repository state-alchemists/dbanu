"""
Core engine abstractions
"""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class SelectEngine(ABC):
    """Abstract base class for database query engines"""

    @abstractmethod
    def select(self, query: str, *params: Any) -> list[Any]:
        """Execute a SELECT query and return results"""
        pass

    @abstractmethod
    def select_count(self, query: str, *params: Any) -> int:
        """Execute a COUNT query and return the count"""
        pass


class QueryContext(BaseModel):
    """
    Context object passed to middlewares, containing all query-related data
    that can be modified by middleware.
    """

    select_query: str
    select_params: list[Any] | None = None
    count_query: str | None = None
    count_params: list[Any] | None = None
    filters: BaseModel
    limit: int
    offset: int
    dependency_results: dict[str, Any]
