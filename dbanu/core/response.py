"""
Response models for DBAnu
"""

from typing import Any

from pydantic import BaseModel, create_model


def create_select_response_model(
    model_name: str, data_model: type[BaseModel] | None = None
):
    """Create a response model for select endpoints"""
    actual_data_model = (
        create_model(f"{model_name}Data") if data_model is None else data_model
    )
    return create_model(
        model_name, data=(list[actual_data_model] | list[Any], ...), count=(int, ...)
    )
