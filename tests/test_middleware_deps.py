from typing import Any
from fastapi import FastAPI, Header, Depends, HTTPException
from fastapi.testclient import TestClient
from dbanu.api import serve_select
from dbanu.core import SelectEngine, QueryContext

class MockQueryEngine(SelectEngine):
    def select(self, query: str, *params: Any) -> list[Any]:
        return [{"id": 1, "title": "Test Book"}]
    def select_count(self, query: str, *params: Any) -> int:
        return 1

async def get_token(x_token: str = Header(None)):
    if x_token != "valid-token":
        raise HTTPException(status_code=401, detail="Invalid token")
    return x_token

async def auth_middleware(context: QueryContext, next_handler):
    token = context.middleware_dependency_results.get("get_token")
    if not token:
        raise HTTPException(status_code=401, detail="Token not found in middleware results")
    return await next_handler(context)

def test_middleware_dependency_with_header():
    app = FastAPI()
    engine = MockQueryEngine()
    
    serve_select(
        app=app,
        query_engine=engine,
        path="/test",
        select_query="SELECT * FROM books",
        middleware_dependencies=[Depends(get_token)],
        middlewares=[auth_middleware]
    )
    
    client = TestClient(app)
    
    # This should work if the dependency is correctly handled
    response = client.get("/test", headers={"x-token": "valid-token"})
    assert response.status_code == 200
    assert response.json()["data"][0]["title"] == "Test Book"

def test_middleware_dependency_invalid_token():
    app = FastAPI()
    engine = MockQueryEngine()
    
    serve_select(
        app=app,
        query_engine=engine,
        path="/test",
        select_query="SELECT * FROM books",
        middleware_dependencies=[Depends(get_token)],
        middlewares=[auth_middleware]
    )
    
    client = TestClient(app)
    
    response = client.get("/test", headers={"x-token": "invalid-token"})
    assert response.status_code == 401
