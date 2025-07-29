# app/models/calculation.py

from sqlalchemy import Column, Float, Enum, ForeignKey, String, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base  # or declarative_base()
from app.schemas.CalculationCreate import CalculationType


class Calculation(Base):
    __tablename__ = "calculations"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    a = Column(Float, nullable=False)
    b = Column(Float, nullable=False)
    type = Column(Enum(CalculationType), nullable=False)
    result = Column(Float, nullable=True)

    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="calculations")  # if defined on User side
