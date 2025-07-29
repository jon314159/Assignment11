import uuid
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.calculation import Calculation
from app.schemas.CalculationCreate import CalculationType
from app.database import Base
from app.models.user import User  # this makes sure 'users' table is registered



# In-memory SQLite engine
engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def setup_module():
    Base.metadata.create_all(bind=engine)


def teardown_module():
    Base.metadata.drop_all(bind=engine)


def test_calculation_model_creation():
    session = TestingSessionLocal()

    new_calc = Calculation(
        a=8.0,
        b=4.0,
        type=CalculationType.DIVIDE,
        result=2.0,
        user_id=uuid.uuid4()
    )

    session.add(new_calc)
    session.commit()
    session.refresh(new_calc)

    assert new_calc.id is not None
    assert new_calc.result == 2.0
    assert new_calc.type == CalculationType.DIVIDE
    assert isinstance(new_calc.created_at, datetime)
    assert isinstance(new_calc.updated_at, datetime)

    session.close()
