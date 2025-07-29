import os
from datetime import datetime, timedelta, timezone
import uuid
from typing import Optional, Dict, Any
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext
from jose import jwt, JWTError
from pydantic import ValidationError

from app.database import Base  # ✅ FIXED: now using shared Base
from app.schemas.base import UserCreate
from app.schemas.user import UserResponse, Token

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Load secret key from environment variables
SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-fallback-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))


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
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    calculations = relationship("Calculation", back_populates="user", cascade="all, delete-orphan")
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email})>" #pragma: no cover

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        return pwd_context.hash(password)

    def verify_password(self, password: str) -> bool:
        """Verify a password against the hashed password."""
        # Defensive check to avoid passing Column object
        if not isinstance(self.hashed_password, str): #pragma: no cover
            raise TypeError(
                f"Invalid hashed_password type: expected str, got {type(self.hashed_password)}"
            )
        return pwd_context.verify(password, self.hashed_password) #pragma: no cover

    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str: #pragma: no cover
        """Create a JWT access token."""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    @classmethod
    def register(cls, db, user_data: Dict[str, Any]) -> "User":
        """Register a new user."""
        try:
            # Validate user data with Pydantic
            user_create = UserCreate.model_validate(user_data)

            # Check for existing user
            existing_user = db.query(cls).filter(
                (cls.username == user_create.username) |
                (cls.email == user_create.email)
            ).first()
            if existing_user:
                raise ValueError("Username or email already exists")

            # Extract and hash password
            password = user_create.password
            hashed_password = cls.hash_password(password)

            # Create new user instance
            new_user = cls(
                first_name=user_create.first_name,
                last_name=user_create.last_name,
                email=user_create.email,
                username=user_create.username,
                hashed_password=hashed_password,
                is_verified=False,
                created_at=datetime.now(timezone.utc)
            )

            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            return new_user

        except ValidationError as e:
            db.rollback()
            raise ValueError(f"Validation error: {str(e)}")

        except IntegrityError as e: #pragma: no cover
            db.rollback()
            # Unify the message
            raise ValueError("Username or email already exists")

        except Exception as e:
            db.rollback()
            raise ValueError(f"Registration failed: {str(e)}")


    @classmethod
    def authenticate(cls, db, identifier: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user by username or email and return token with user data."""
        try:
            user = db.query(cls).filter(
                (cls.username == identifier) | (cls.email == identifier)
            ).first()

            # Ensure instance exists and password matches
            if not user or not user.verify_password(password):
                return None

            # Update last login timestamp
            user.last_login = datetime.now(timezone.utc)
            db.commit()
            db.refresh(user)

            # Create response objects
            user_response = UserResponse.model_validate(user)
            token_response = Token(
                access_token=cls.create_access_token(data={"sub": str(user.id)}),
                token_type="bearer",
                user=user_response
            )

            return token_response.model_dump()

        except Exception as e: #pragma: no cover
            db.rollback()
            # Log the error but don't expose internal details
            # logger.error(f"Authentication error: {str(e)}")
            return None

    @classmethod
    def verify_token(cls, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            return None

    @classmethod
    def get_user_by_id(cls, db, user_id: str) -> Optional["User"]:
        """Get user by ID."""
        try:
            user_uuid = uuid.UUID(user_id)
            return db.query(cls).filter(cls.id == user_uuid).first()
        except (ValueError, TypeError):
            return None

    def update_last_login(self, db):
        """Update the user's last login timestamp."""
        self.last_login = datetime.now(timezone.utc)
        db.commit()

    def to_dict(self) -> Dict[str, Any]:
        """Convert user object to dictionary (excluding sensitive data)."""
        return { #pragma: no cover
            "id": str(self.id),
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "username": self.username,
            "is_verified": self.is_verified,
            "last_login": self.last_login.isoformat() if self.last_login is not None else None,
            "created_at": self.created_at.isoformat() if self.created_at is not None else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at is not None else None,
        }