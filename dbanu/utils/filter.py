from pydantic import BaseModel, Field, create_model


def enhance_select_filter(base_cls: type[BaseModel], default_limit: int | None):
    limit_field = (
        int,
        Field(default=default_limit if default_limit is not None else 100, ge=1),
    )
    offset_field = (int, Field(default=0, ge=0))
    if not hasattr(base_cls, "limit") and not hasattr(base_cls, "offset"):
        return create_model(
            base_cls.__name__, __base__=base_cls, limit=limit_field, offset=offset_field
        )
    if not hasattr(base_cls, "limit"):
        return create_model(
            base_cls.__name__,
            __base__=base_cls,
            limit=limit_field,
        )
    if not hasattr(base_cls, "offset"):
        return create_model(base_cls.__name__, __base__=base_cls, offset=offset_field)
    return base_cls


def enhance_union_filter(base_cls: type[BaseModel], default_limit: int | None):
    new_base_cls = enhance_select_filter(base_cls, default_limit)
    if not hasattr(base_cls, "sources"):
        return create_model(
            new_base_cls.__name__,
            __base__=new_base_cls,
            sources=(str | None, None),
        )
    return new_base_cls
