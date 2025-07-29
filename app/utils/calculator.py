# app/utils/calculator.py

from app.operations import add, subtract, multiply, divide
from app.schemas.CalculationCreate import CalculationType


class CalculationStrategy:
    def compute(self, a: float, b: float) -> float:
        raise NotImplementedError


class Add(CalculationStrategy):
    def compute(self, a: float, b: float) -> float:
        return add(a, b)


class Sub(CalculationStrategy):
    def compute(self, a: float, b: float) -> float:
        return subtract(a, b)


class Multiply(CalculationStrategy):
    def compute(self, a: float, b: float) -> float:
        return multiply(a, b)


class Divide(CalculationStrategy):
    def compute(self, a: float, b: float) -> float:
        return divide(a, b)


class CalculationFactory:
    @staticmethod
    def get_strategy(calc_type: CalculationType) -> CalculationStrategy:
        match calc_type:
            case CalculationType.ADD:
                return Add()
            case CalculationType.SUB:
                return Sub()
            case CalculationType.MULTIPLY:
                return Multiply()
            case CalculationType.DIVIDE:
                return Divide()
            case _:
                raise ValueError(f"Unsupported calculation type: {calc_type}")
