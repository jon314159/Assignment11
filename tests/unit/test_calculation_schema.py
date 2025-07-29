from uuid import UUID
from datetime import datetime
import pytest
from pydantic import ValidationError

from app.schemas.CalculationCreate import CalculationType, CalculationCreate
from app.schemas.CalcylationResponse import CalculationRead


def test_calculation_read_valid_data():
    data = {
        "id": "de305d54-75b4-431b-adb2-eb6b9e546014",
        "a": 12.5,
        "b": 2.5,
        "type": "Divide",
        "result": 5.0,
        "user_id": "abc12345-6789-4abc-def0-1234567890ab",
        "created_at": "2023-10-01T12:00:00Z",
        "updated_at": "2023-10-01T13:00:00Z"
    }

    calc = CalculationRead(**data)

    assert isinstance(calc.id, UUID)
    assert isinstance(calc.user_id, UUID)
    assert calc.type == CalculationType.DIVIDE
    assert calc.result == 5.0
    assert isinstance(calc.created_at, datetime)
    assert isinstance(calc.updated_at, datetime)


def test_invalid_enum_type():
    data = {
        "id": "de305d54-75b4-431b-adb2-eb6b9e546014",
        "a": 12.5,
        "b": 2.5,
        "type": "BadType",  # invalid enum
        "result": 5.0,
        "user_id": "abc12345-6789-4abc-def0-1234567890ab",
        "created_at": "2023-10-01T12:00:00Z"
    }

    with pytest.raises(ValidationError):
        CalculationRead(**data)


def test_divide_by_zero_validation_error():
    with pytest.raises(ValueError, match="Cannot divide by zero."):
        CalculationCreate(a=10, b=0, type=CalculationType.DIVIDE)


def test_valid_division_passes():
    calc = CalculationCreate(a=10, b=2, type=CalculationType.DIVIDE)
    assert calc.a == 10
    assert calc.b == 2
    assert calc.type == CalculationType.DIVIDE
