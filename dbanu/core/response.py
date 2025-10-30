"""
Response models for DBAnu
"""

from typing import Any

from pydantic import BaseModel, create_model


def create_select_response_model(data_model: type[BaseModel] | None = None):
    """Create a response model for select endpoints"""
    actual_data_model = create_model("DataModel") if data_model is None else data_model

    class SelectResponseModel(BaseModel):
        data: list[actual_data_model] | list[Any]  # type: ignore
        count: int

    return SelectResponseModel
