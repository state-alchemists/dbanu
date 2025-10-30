"""
Middleware system for DBAnu
"""

import inspect
from typing import Any, Callable

from dbanu.core.engine import QueryContext

# Middleware type that receives QueryContext and next middleware callable
# and returns the ResponseModel (data_model)
Middleware = Callable[[QueryContext, Callable[[QueryContext], Any]], Any]


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
        # Check if the middleware is async
        if inspect.iscoroutinefunction(current_middleware):
            return await current_middleware(context, lambda ctx: next_handler(ctx))
        else:
            return current_middleware(context, lambda ctx: next_handler(ctx))

    return wrapper


def get_combined_middlewares(
    global_middlewares: list[Middleware] | None,
    local_middlewares: list[Middleware] | None,
) -> list[Middleware] | None:
    """Combine global and local middlewares"""
    normalized_global_middlewares = global_middlewares or []
    normalized_local_middlewares = local_middlewares or []
    return list(normalized_global_middlewares) + list(normalized_local_middlewares)
