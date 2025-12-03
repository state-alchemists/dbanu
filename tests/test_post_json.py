#!/usr/bin/env python3
"""
Tests for POST requests with JSON body support
"""
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from dbanu.api import SelectSource, serve_select, serve_union
from dbanu.core import SelectEngine


class MockQueryEngine(SelectEngine):
    """Mock query engine for testing"""

    def __init__(self, data, count):
        self.data = data
        self.count = count
        self.last_select_params = None
        self.last_count_params = None

    def select(self, query: str, *params: Any) -> list[Any]:
        self.last_select_params = params
        limit = params[-2] if len(params) >= 2 else len(self.data)
        offset = params[-1] if len(params) >= 1 else 0
        return self.data[offset : offset + limit]

    def select_count(self, query: str, *params: Any) -> int:
        self.last_count_params = params
        return self.count


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


class TestPostJsonSupport:
    """Test cases for POST requests with JSON body"""

    def test_serve_select_post_json_body(self):
        """Test serve_select with POST method and JSON body"""
        app = FastAPI()
        mock_engine = MockQueryEngine(
            data=[
                {"id": 1, "title": "Book 1", "author": "Author A", "year": 2020},
                {"id": 2, "title": "Book 2", "author": "Author B", "year": 2021},
            ],
            count=2
        )
        
        # Register endpoint with POST method
        serve_select(
            app=app,
            query_engine=mock_engine,
            path="/api/books",
            filter_model=BookFilter,
            data_model=BookData,
            select_query=(
                "SELECT id, title, author, year FROM books "
                "WHERE (author = %s OR %s IS NULL) "
                "AND (year > %s OR %s IS NULL) "
                "AND (year < %s OR %s IS NULL) "
                "LIMIT %s OFFSET %s"
            ),
            count_query=(
                "SELECT COUNT(*) FROM books "
                "WHERE (author = %s OR %s IS NULL) "
                "AND (year > %s OR %s IS NULL) "
                "AND (year < %s OR %s IS NULL) "
            ),
            methods=["post"],
            param=["author", "author", "min_year", "min_year", "max_year", "max_year"]
        )
        
        client = TestClient(app)
        
        # Test POST request with JSON body
        response = client.post(
            "/api/books",
            json={
                "author": "Author A",
                "min_year": 2019,
                "max_year": 2022
            },
            params={"limit": 10, "offset": 0}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "count" in data
        assert len(data["data"]) == 2
        
        # Verify parameters were parsed correctly from JSON body
        # The first 6 params should come from the filter, last 2 are limit/offset
        assert mock_engine.last_select_params is not None
        assert len(mock_engine.last_select_params) == 8  # 6 filter params + 2 pagination
        assert mock_engine.last_select_params[0] == "Author A"  # author
        assert mock_engine.last_select_params[1] == "Author A"  # author (for IS NULL check)
        assert mock_engine.last_select_params[2] == 2019  # min_year
        assert mock_engine.last_select_params[3] == 2019  # min_year (for IS NULL check)
        assert mock_engine.last_select_params[4] == 2022  # max_year
        assert mock_engine.last_select_params[5] == 2022  # max_year (for IS NULL check)
        assert mock_engine.last_select_params[6] == 10  # limit
        assert mock_engine.last_select_params[7] == 0   # offset
        
        # Count params should also be correct
        assert mock_engine.last_count_params is not None
        assert len(mock_engine.last_count_params) == 6  # Only filter params, no pagination
        assert mock_engine.last_count_params[0] == "Author A"
        assert mock_engine.last_count_params[1] == "Author A"
        assert mock_engine.last_count_params[2] == 2019
        assert mock_engine.last_count_params[3] == 2019
        assert mock_engine.last_count_params[4] == 2022
        assert mock_engine.last_count_params[5] == 2022

    def test_serve_select_get_still_works(self):
        """Test that GET requests still work with query parameters"""
        app = FastAPI()
        mock_engine = MockQueryEngine(
            data=[{"id": 1, "title": "Book 1", "author": "Author A", "year": 2020}],
            count=1
        )
        
        # Register endpoint with GET method (default)
        serve_select(
            app=app,
            query_engine=mock_engine,
            path="/api/books",
            filter_model=BookFilter,
            data_model=BookData,
            select_query="SELECT * FROM books LIMIT %s OFFSET %s",
            count_query="SELECT count(1) FROM books",
            methods=["get"],
        )
        
        client = TestClient(app)
        
        # Test GET request with query parameters
        response = client.get(
            "/api/books",
            params={
                "author": "Author A",
                "min_year": 2019,
                "max_year": 2022,
                "limit": 10,
                "offset": 0
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "count" in data

    def test_serve_union_post_json_body(self):
        """Test serve_union with POST method and JSON body"""
        app = FastAPI()
        
        # Create mock sources
        source1_engine = MockQueryEngine(data=["s1-r1", "s1-r2"], count=2)
        source2_engine = MockQueryEngine(data=["s2-r1", "s2-r2", "s2-r3"], count=3)
        
        serve_union(
            app=app,
            sources={
                "source-1": SelectSource(
                    query_engine=source1_engine,
                    select_query="SELECT * FROM table LIMIT %s OFFSET %s",
                    count_query="SELECT COUNT(*) FROM table",
                ),
                "source-2": SelectSource(
                    query_engine=source2_engine,
                    select_query="SELECT * FROM table LIMIT %s OFFSET %s",
                    count_query="SELECT COUNT(*) FROM table",
                ),
            },
            path="/api/union/books",
            filter_model=BookFilter,
            data_model=BaseModel,  # Simple model for test
            methods=["post"],
        )
        
        client = TestClient(app)
        
        # Test POST request with JSON body
        response = client.post(
            "/api/union/books",
            json={
                "author": "Author A",
                "min_year": 2019,
                "max_year": 2022
            },
            params={"limit": 5, "offset": 0}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "count" in data
        assert data["count"] == 5  # 2 + 3

    def test_mixed_methods_get_and_post(self):
        """Test that endpoints with both GET and POST methods work"""
        app = FastAPI()
        mock_engine = MockQueryEngine(
            data=[{"id": 1, "title": "Book 1", "author": "Author A", "year": 2020}],
            count=1
        )
        
        # Register endpoint with both GET and POST methods
        serve_select(
            app=app,
            query_engine=mock_engine,
            path="/api/books",
            filter_model=BookFilter,
            data_model=BookData,
            select_query="SELECT * FROM books LIMIT %s OFFSET %s",
            count_query="SELECT count(1) FROM books",
            methods=["get", "post"],
        )
        
        client = TestClient(app)
        
        # Test GET request
        response_get = client.get(
            "/api/books",
            params={
                "author": "Author A",
                "limit": 10,
                "offset": 0
            }
        )
        assert response_get.status_code == 200
        
        # Test POST request with JSON body
        response_post = client.post(
            "/api/books",
            json={"author": "Author A"},
            params={"limit": 10, "offset": 0}
        )
        assert response_post.status_code == 200