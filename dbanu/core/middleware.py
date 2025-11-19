"""
Middleware system for DBAnu
"""

import inspect
from typing import Any, Callable

from dbanu.core.engine import QueryContext

# Middleware type that receives QueryContext and next middleware callable
# and returns the ResponseModel (data_model)
Middleware = Callable[[QueryContext, Callable[[QueryContext], Any]], Any]


def validate_middlewares(middlewares: list[Middleware] | None) -> None:
    """Validate that all middleware functions are async"""
    if middlewares is None:
        return

    for i, middleware in enumerate(middlewares):
        if not inspect.iscoroutinefunction(middleware):
            raise TypeError(
                f"Middleware at index {i} must be an async function. "
                f"Got: {type(middleware).__name__}. "
                f"Please define your middleware with 'async def'."
            )


def create_middleware_chain(
    middlewares: list[Middleware] | None, final_handler: Callable[[QueryContext], Any]
):
    """Create a middleware chain from a list of middlewares"""
    handler = final_handler
    if middlewares is None:
        middlewares = []
    for middleware in reversed(middlewares):
        handler = _make_middleware_wrapper(middleware, handler)
    return handler


def _make_middleware_wrapper(
    current_middleware: Middleware, next_handler: Callable[[QueryContext], Any]
):
    """Wrap a middleware with the next handler"""

    async def wrapper(context: QueryContext):
        # Create an async-compatible next_handler
        async def async_next_handler(ctx):
            result = next_handler(ctx)
            if inspect.iscoroutine(result):
                return await result
            return result

        # All middleware should be async now
        return await current_middleware(context, async_next_handler)

    return wrapper


def get_combined_middlewares(
    global_middlewares: list[Middleware] | None,
    local_middlewares: list[Middleware] | None,
) -> list[Middleware] | None:
    """Combine global and local middlewares"""
    normalized_global_middlewares = global_middlewares or []
    normalized_local_middlewares = local_middlewares or []
    return list(normalized_global_middlewares) + list(normalized_local_middlewares)
