from datetime import datetime, timedelta
import uuid
from typing import Optional, Dict, Any

from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import declarative_base
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext
from jose import jwt
from pydantic import ValidationError

from app.schemas.base import UserCreate
from app.schemas.user import UserResponse, Token

Base = declarative_base()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "your_secret_key_here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class User(Base):
    """User model for the application."""
    __tablename__ = "users"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String, nullable=False, index=True)
    last_name = Column(String, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        return pwd_context.hash(password)

    def verify_password(self, password: str) -> bool:
        """Verify a password against the hashed password."""
        return pwd_context.verify(password, self.password)

    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    @classmethod
    def register(cls, db, user_data: Dict[str, Any]) -> "User":
        """Register a new user."""
        try:
            password = user_data.pop("password")

            if len(password) < 8:
                raise ValueError("Password must be at least 8 characters long.")
            if len(password) > 128:
                raise ValueError("Password must not exceed 128 characters.")

            existing_user = db.query(cls).filter(
                (cls.username == user_data["username"]) |
                (cls.email == user_data["email"])
            ).first()
            if existing_user:
                raise ValueError("Username or email already exists.")

            user_create = UserCreate.model_validate(user_data)
            new_user = cls(
                first_name=user_create.first_name,
                last_name=user_create.last_name,
                email=user_create.email,
                username=user_create.username,
                hashed_password=cls.hash_password(password),
                is_verified=user_create.model_dump().get("is_verified", False),
                created_at=datetime.utcnow()
            )

            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            return new_user

        except ValidationError as e:
            raise ValueError(f"Validation error: {e}")
        except IntegrityError as e:
            raise ValueError(f"Integrity error: {e.orig}")
        except ValueError as e:
            raise ValueError(f"Value error: {e}")

    @classmethod
    def authenticate(cls, db, identifier: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user by username or email and return token with user data."""
        user = db.query(cls).filter(
            (cls.username == identifier) | (cls.email == identifier)
        ).first()

        if not user or not user.verify_password(password):
            return None  # pragma: no cover

        user.last_login = datetime.utcnow()
        db.commit()
        db.refresh(user)

        user_response = UserResponse.model_validate(user)
        token_response = Token(
            access_token=cls.create_access_token(data={"sub": str(user.id)}),
            token_type="bearer",
            user=user_response
        )

        return token_response.model_dump()
