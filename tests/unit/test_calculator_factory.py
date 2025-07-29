import pytest
from app.utils.calculator import Add, Sub, Multiply, Divide, CalculationFactory
from app.schemas.enums import CalculationType  # ✅ now imports clean enum only


def test_add():
    strategy = Add()
    assert strategy.compute(10, 5) == 15


def test_subtract():
    strategy = Sub()
    assert strategy.compute(10, 5) == 5


def test_multiply():
    strategy = Multiply()
    assert strategy.compute(10, 5) == 50


def test_divide():
    strategy = Divide()
    assert strategy.compute(10, 2) == 5


def test_divide_by_zero_raises():
    strategy = Divide()
    with pytest.raises(ValueError, match="Cannot divide by zero."):
        strategy.compute(10, 0)


def test_factory_returns_add():
    strategy = CalculationFactory.get_strategy(CalculationType.ADD)
    assert isinstance(strategy, Add)


def test_factory_returns_sub():
    strategy = CalculationFactory.get_strategy(CalculationType.SUB)
    assert isinstance(strategy, Sub)


def test_factory_returns_multiply():
    strategy = CalculationFactory.get_strategy(CalculationType.MULTIPLY)
    assert isinstance(strategy, Multiply)


def test_factory_returns_divide():
    strategy = CalculationFactory.get_strategy(CalculationType.DIVIDE)
    assert isinstance(strategy, Divide)


def test_factory_invalid_type_raises():
    with pytest.raises(ValueError):
        CalculationFactory.get_strategy("FakeType")  # type: ignore[arg-type]
