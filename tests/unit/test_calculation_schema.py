from uuid import UUID
from datetime import datetime
from app.schemas.CalculationCreate import  CalculationType
from app.schemas.CalcylationResponse  import CalculationRead


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

    from pydantic import ValidationError
    import pytest

    with pytest.raises(ValidationError):
        CalculationRead(**data)
