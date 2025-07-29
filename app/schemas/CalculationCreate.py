from enum import Enum
from pydantic import BaseModel, ConfigDict, model_validator


class CalculationType(str, Enum):
    ADD = "Add"
    SUB = "Sub"
    MULTIPLY = "Multiply"
    DIVIDE = "Divide"


class CalculationCreate(BaseModel):
    """Schema for creating a new calculation"""
    a: float
    b: float
    type: CalculationType

    @model_validator(mode='after')
    def validate_division(self):
        if self.type == CalculationType.DIVIDE and self.b == 0:
            raise ValueError("Cannot divide by zero.")
        return self

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "a": 12.5,
                "b": 2.5,
                "type": "Divide"
            }
        }
    )
