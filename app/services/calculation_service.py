# app/services/calculation_service.py

from sqlalchemy.orm import Session
from app.models.calculation import Calculation
from app.utils.calculator import CalculationFactory
from app.schemas.CalculationCreate import CalculationCreate


def create_calculation(payload: CalculationCreate, user_id: str, db: Session) -> Calculation:
    strategy = CalculationFactory.get_strategy(payload.type)
    result = strategy.compute(payload.a, payload.b)

    new_calc = Calculation(
        a=payload.a,
        b=payload.b,
        type=payload.type,
        result=result,
        user_id=user_id,
    )

    db.add(new_calc)
    db.commit()
    db.refresh(new_calc)
    return new_calc
