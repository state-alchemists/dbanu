"""
Dependency injection utilities for DBAnu
"""

import inspect
from typing import Any

from fastapi import Depends, Request


def create_wrapped_fastapi_dependencies(dependencies: list[Any] | None):
    """Create wrapped dependencies that store results in request state"""
    if dependencies is None:
        return []
    wrapped_dependencies = []
    for dep in dependencies:
        # Create a closure-safe wrapper for each dependency
        def create_wrapped_dependency(original_dep):
            async def wrapped_dependency(request: Request):
                # Extract the actual dependency function from Depends object
                if hasattr(original_dep, "dependency"):
                    dependency_func = original_dep.dependency
                else:
                    dependency_func = original_dep

                # Execute the dependency
                if inspect.iscoroutinefunction(dependency_func):
                    result = await dependency_func()
                else:
                    result = dependency_func()

                # Store the result in request state
                if not hasattr(request.state, "dependency_results"):
                    request.state.dependency_results = {}

                # Use the dependency function name as key
                dep_name = dependency_func.__name__
                request.state.dependency_results[dep_name] = result
                return result

            return wrapped_dependency

        wrapped_dependencies.append(Depends(create_wrapped_dependency(dep)))

    return wrapped_dependencies
