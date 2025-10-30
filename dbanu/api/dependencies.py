"""
Dependency injection utilities for DBAnu
"""

from typing import Any

from fastapi import Depends, Request


def create_wrapped_fastapi_dependencies(dependencies: list[Any] | None):
    """Create wrapped dependencies that store results in request state"""
    if dependencies is None:
        return []
    wrapped_dependencies = []
    for dep in dependencies:
        if hasattr(dep, "dependency"):
            # Create a closure-safe wrapper for each dependency
            def create_wrapped_dependency(original_dep):
                async def wrapped_dependency(request: Request):
                    result = await original_dep.dependency
                    # Store the result in request state
                    if not hasattr(request.state, "dependency_results"):
                        request.state.dependency_results = {}
                    # Use the dependency function name as key
                    dep_name = original_dep.dependency.__name__
                    request.state.dependency_results[dep_name] = result
                    return result

                return wrapped_dependency

            wrapped_dependencies.append(Depends(create_wrapped_dependency(dep)))
        else:
            wrapped_dependencies.append(dep)

    return wrapped_dependencies
