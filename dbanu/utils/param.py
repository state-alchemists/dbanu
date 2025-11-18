from typing import Any, Callable

from pydantic import BaseModel


def get_parsed_count_params(
    filter: BaseModel,
    count_param: Callable[[Any], list[Any]] | list[str] | None,
    base_param: Callable[[Any], list[Any]] | list[str] | None,
) -> list[Any]:
    param = count_param if count_param is not None else base_param
    if param is None:
        return []
    if callable(param):
        return param(filter)
    if isinstance(param, list):
        parsed_param = []
        for attr in param:
            if not hasattr(filter, attr):
                raise ValueError(f"{filter} doesn't have {attr}")
            parsed_param.append(getattr(filter, attr))
        return parsed_param
    return []


def get_parsed_select_params(
    filter: BaseModel,
    limit: int,
    offset: int,
    select_param: Callable[[Any, int, int], list[Any]] | list[str] | None,
    base_param: Callable[[Any], list[Any]] | list[str] | None,
) -> list[Any]:
    if select_param is None and base_param is None:
        return [limit, offset]
    if select_param is not None:
        if callable(select_param):
            return select_param(filter, limit, offset)
        if isinstance(select_param, list):
            parsed_param = []
            for attr in select_param:
                if attr == "limit":
                    parsed_param.append(limit)
                    continue
                if attr == "offset":
                    parsed_param.append(offset)
                    continue
                if not hasattr(filter, attr):
                    raise ValueError(f"{filter} doesn't have {attr}")
                parsed_param.append(getattr(filter, attr))
            return parsed_param
        return [limit, offset]
    if base_param is not None:
        if callable(base_param):
            return base_param(filter) + [limit, offset]
        if isinstance(base_param, list):
            parsed_param = []
            for attr in base_param:
                if not hasattr(filter, attr):
                    raise ValueError(f"{filter} doesn't have {attr}")
                parsed_param.append(getattr(filter, attr))
            return parsed_param + [limit, offset]
    return [limit, offset]
