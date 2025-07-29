import uuid
from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.user import User
from app.models.calculation import Calculation
from app.schemas.enums import CalculationType  # Make sure this enum doesn't import models
from app.database import Base

# Create in-memory SQLite engine
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module", autouse=True)
def setup_and_teardown():
    # Create all tables
    Base.metadata.create_all(bind=engine)
    yield
    # Drop all tables after tests
    Base.metadata.drop_all(bind=engine)


def test_calculation_model_creation():
    session = TestingSessionLocal()

    # Create test user
    user = User(
        id=uuid.uuid4(),
        first_name="Test",
        last_name="User",
        email="testuser@example.com",
        username="testuser",
        hashed_password="not_real"
    )
    session.add(user)
    session.commit()

    # Create test calculation
    new_calc = Calculation(
        a=8.0,
        b=4.0,
        type=CalculationType.DIVIDE,
        result=2.0,
        user_id=user.id
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
