from pydantic import BaseModel
from typing import Any, Callable


def get_count_param_list(
    filter: BaseModel,
    limit: int,
    offset: int,
    count_param: Callable[[BaseModel], list[Any]] | list[str] | None,
    base_param: Callable[[BaseModel], list[Any]] | list[str] | None,
) -> list[Any]:
    return []


def get_select_param_list(
    filter: BaseModel,
    limit: int,
    offset: int,
    select_param: Callable[[BaseModel, int, int], list[Any]] | list[str] | None,
    base_param: Callable[[BaseModel], list[Any]] | list[str] | None,
) -> list[Any]:
    return []