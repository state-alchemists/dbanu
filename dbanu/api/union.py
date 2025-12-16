import inspect
import traceback
from typing import Any, Callable, Type, TypeVar

from fastapi import Body, Depends, FastAPI, HTTPException, Request
from pydantic import BaseModel, Field, create_model

from dbanu.api.dependencies import create_wrapped_fastapi_dependencies
from dbanu.core.engine import QueryContext, SelectEngine
from dbanu.core.middleware import (
    Middleware,
    create_middleware_chain,
    get_combined_middlewares,
    validate_middlewares,
)
from dbanu.core.response import create_select_response_model
from dbanu.utils.filter import enhance_union_filter
from dbanu.utils.pagination import calculate_union_pagination
from dbanu.utils.param import get_parsed_count_params, get_parsed_select_params
from dbanu.utils.string import to_var_name

Filter = TypeVar("Filter", bound=BaseModel)


class SelectSource(BaseModel):
    """Configuration for a single data source in union queries"""

    model_config = {"arbitrary_types_allowed": True}
    query_engine: SelectEngine
    select_query: str | Callable[[BaseModel], str]
    select_param: Callable[[BaseModel, int, int], list[Any]] | list[str] | None = None
    count_query: str | Callable[[BaseModel], str]
    count_param: Callable[[BaseModel], list[Any]] | list[str] | None = None
    param: Callable[[BaseModel], list[Any]] | list[str] | None = None
    middlewares: list[Middleware] | None = None

    def __init__(self, **data):
        super().__init__(**data)
        # Validate that all middlewares are async functions
        validate_middlewares(self.middlewares)


def serve_union(
    app: FastAPI,
    sources: dict[str, SelectSource],
    path: str = "/get",
    methods: list[str] | None = None,
    filter_model: Type[BaseModel] | None = None,
    data_model: Type[BaseModel] | None = None,
    response_model: Type[BaseModel] | None = None,
    dependencies: list[Any] | None = None,
    middlewares: list[Middleware] | None = None,
    source_priority: list[str] | None = None,
    name: str | None = None,
    summary: str | None = None,
    description: str | None = None,
    default_limit: int | None = None,
):
    """
    Create a union endpoint that combines results from multiple sources
    with priority-based pagination
    """
    methods = ["GET"] if methods is None else [m.upper() for m in methods]
    var_name = to_var_name(name, path)
    if filter_model is None:
        filter_model = create_model(
            "FilterModel" if var_name is None else f"{var_name.capitalize()}Filter",
        )
    filter_model = enhance_union_filter(filter_model, default_limit)
    if response_model is None:
        response_model = create_select_response_model(
            "ResponseModel" if var_name is None else f"{var_name.capitalize()}Response",
            data_model,
        )
    wrapped_dependencies = create_wrapped_fastapi_dependencies(dependencies)
    # Validate that all middlewares are async functions
    validate_middlewares(middlewares)

    # Create the actual handler function
    async def handle_request(
        request: Request,
        filter_data: filter_model,  # type: ignore
    ):
        """Union handler"""
        # Get params from filters
        limit = getattr(filter_data, "limit", 100)
        offset = getattr(filter_data, "offset", 0)
        selected_source_priority = getattr(filter_data, "sources", None)
        # Extract dependency results from request state
        dependency_results = {}
        if request and hasattr(request.state, "dependency_results"):
            dependency_results = request.state.dependency_results
        priority_list = _get_priority_list(selected_source_priority, source_priority, sources)
        # Step 1: Get total count from each source
        source_counts = {}
        total_count = 0
        for source_name in priority_list:
            source = sources[source_name]
            count_query_str = (
                source.count_query(filter_data)
                if callable(source.count_query)
                else source.count_query
            )
            parsed_count_params = get_parsed_count_params(
                filter_data, source.count_param, source.param
            )
            count_context = QueryContext(
                select_query="",
                select_params=[],
                count_query=count_query_str,
                count_params=parsed_count_params,
                filters=filter_data,
                limit=0,
                offset=0,
                dependency_results=dependency_results,
            )
            count_processor = _create_count_processor(source.query_engine)
            handler = create_middleware_chain(source.middlewares, count_processor)
            source_count = await handler(count_context)
            source_counts[source_name] = source_count
            total_count += source_count
        # Step 2: Calculate which records to fetch from each source
        fetch_plan = calculate_union_pagination(
            source_counts, priority_list, limit, offset
        )
        # Step 3: Fetch data according to the plan
        final_data = []
        for source_name, (source_limit, source_offset) in fetch_plan.items():
            source = sources[source_name]
            # Build select parameters for this specific source
            select_query_str = (
                source.select_query(filter_data)
                if callable(source.select_query)
                else source.select_query
            )
            parsed_select_params = get_parsed_select_params(
                filter_data,
                source_limit,
                source_offset,
                source.select_param,
                source.param,
            )
            # Create QueryContext for this source
            select_context = QueryContext(
                select_query=select_query_str,
                select_params=parsed_select_params,
                count_query="",
                count_params=[],
                filters=filter_data,
                limit=source_limit,
                offset=source_offset,
                dependency_results=dependency_results,
            )
            select_processor = _create_select_processor(source.query_engine)
            handler = create_middleware_chain(
                get_combined_middlewares(middlewares, source.middlewares),
                select_processor,
            )
            source_data = await handler(select_context)
            # Add the data to final result
            final_data.extend(source_data)
        return response_model(data=final_data, count=total_count)

    # Register routes based on methods
    if "GET" in methods:

        @app.get(
            path,
            response_model=response_model,
            dependencies=wrapped_dependencies,
            name=None if name is None else f"{name}Get",
            summary=summary,
            description=description,
        )
        async def get_handler(
            request: Request,
            filters: filter_model = Depends(),  # type: ignore
        ):
            """Union route (generated by dbAnu)"""
            try:
                return await handle_request(request, filters)
            except Exception as e:
                traceback.print_exc()
                raise HTTPException(500, f"{e}")

    # Register other methods (POST, PUT, etc.)
    other_methods = [m for m in methods if m != "GET"]
    if other_methods:
        # Create a single route for all non-GET methods
        @app.api_route(
            path,
            methods=other_methods,
            response_model=response_model,
            dependencies=wrapped_dependencies,
            name=name,
            summary=summary,
            description=description,
        )
        async def non_get_handler(
            request: Request,
            filters: filter_model = Body(),  # type: ignore
        ):
            """Union route (generated by dbAnu)"""
            try:
                return await handle_request(request, filters)
            except Exception as e:
                traceback.print_exc()
                raise HTTPException(500, f"{e}")


def _get_priority_list(
    source_priority_str: str | None,
    default_source_priority: list[str] | None,
    sources: dict[str, SelectSource],
) -> list:
    if source_priority_str is not None:
        return [
            source.strip()
            for source in source_priority_str.split(",")
            if source.strip() != ""
            if source in sources
        ]
    if default_source_priority is not None:
        return default_source_priority
    return list(sources.keys())


def _create_select_processor(query_engine: SelectEngine):
    """Create a select processor for the middleware chain"""

    async def process_select(context: QueryContext) -> list[Any]:
        select_params = context.select_params or []
        # Check if select method is a coroutine
        select_method = query_engine.select
        if inspect.iscoroutinefunction(select_method):
            return await select_method(context.select_query, *select_params)
        return select_method(context.select_query, *select_params)

    return process_select


def _create_count_processor(query_engine: SelectEngine):
    """Create a count processor for the middleware chain"""

    async def process_count(context: QueryContext) -> int:
        count_params = context.count_params or []
        if context.count_query is None:
            raise ValueError(f"select_count is not defined at this context: {context}")
        select_count_method = query_engine.select_count
        if inspect.iscoroutinefunction(select_count_method):
            return await select_count_method(context.count_query, *count_params)
        return select_count_method(context.count_query, *count_params)

    return process_count
