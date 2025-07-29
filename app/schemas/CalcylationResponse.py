from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from enum import Enum


class CalculationType(str, Enum):
    ADD = "Add"
    SUB = "Sub"
    MULTIPLY = "Multiply"
    DIVIDE = "Divide"


class CalculationRead(BaseModel):
    """Schema for reading a calculation result"""
    id: UUID
    a: float
    b: float
    type: CalculationType
    result: float
    user_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "de305d54-75b4-431b-adb2-eb6b9e546014",
                "a": 12.5,
                "b": 2.5,
                "type": "Divide",
                "result": 5.0,
                "user_id": "abc12345-6789-4abc-def0-1234567890ab",
                "created_at": "2023-10-01T12:00:00Z",
                "updated_at": "2023-10-01T13:00:00Z"
            }
        }
    )
