from typing import Any, Callable

from pydantic import BaseModel


def get_parsed_count_params(
    filters: BaseModel,
    count_param: Callable[[Any], list[Any]] | list[str] | None,
    base_param: Callable[[Any], list[Any]] | list[str] | None,
) -> list[Any]:
    param = count_param if count_param is not None else base_param
    if param is None:
        return []
    if callable(param):
        return param(filters)
    if isinstance(param, list):
        return [
            _get_attr(filters, attr_name) for attr_name in param
        ]
    return []


def get_parsed_select_params(
    filters: BaseModel,
    limit: int,
    offset: int,
    select_param: Callable[[Any, int, int], list[Any]] | list[str] | None,
    base_param: Callable[[Any], list[Any]] | list[str] | None,
) -> list[Any]:
    if select_param is None and base_param is None:
        return [limit, offset]
    if select_param is not None:
        if callable(select_param):
            return select_param(filters, limit, offset)
        if isinstance(select_param, list):
            parsed_param = []
            for attr_name in select_param:
                if attr_name == "limit":
                    parsed_param.append(limit)
                    continue
                if attr_name == "offset":
                    parsed_param.append(offset)
                    continue
                parsed_param.append(_get_attr(filters, attr_name))
            return parsed_param
        return [limit, offset]
    if base_param is not None:
        if callable(base_param):
            return base_param(filters) + [limit, offset]
        if isinstance(base_param, list):
            return [
                _get_attr(filters, attr_name) for attr_name in base_param
            ] + [limit, offset]
    return [limit, offset]


def _get_attr(obj: Any, attr_names: str) -> Any:
    attr = obj
    for attr_name in attr_names.split("."):
        if not hasattr(attr, attr_name):
            raise ValueError(f"{obj} has no attribute {attr_name}")
        attr = getattr(attr, attr_name)
    return attr
