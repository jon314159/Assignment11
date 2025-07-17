from pydantic import BaseModel, EmailStr, Field, ConfigDict, model_validator, field_validator
from typing import Optional
from uuid import UUID
from datetime import datetime


class UserBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: EmailStr = Field(..., description="User's email address")
    username: str = Field(..., min_length=3, max_length=50, description="Unique username for the user")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        if not v.isalnum():
            raise ValueError("Username must be alphanumeric")
        return v

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "username": "johndoe"
            }
        }
    )


class PasswordMixin(BaseModel):
    password: str = Field(..., min_length=8, max_length=128, description="User's password")

    @model_validator(mode='before')
    @classmethod
    def validate_passwords_match(cls, values):
        password = values.get("password")
        if password is None:
            raise ValueError("Password must be provided")
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if len(password) > 128:
            raise ValueError("Password must not exceed 128 characters")
        if not any(char.isdigit() for char in password):
            raise ValueError("Password must contain at least one digit")
        if not any(char.isupper() for char in password):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(char.islower() for char in password):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(char in "!@#$%^&*()-_=+[]{}|;:,.<>?/" for char in password):
            raise ValueError("Password must contain at least one special character")
        return values


class UserCreate(UserBase, PasswordMixin):
    """Schema for user creation"""
    pass


class UserLogin(PasswordMixin):
    """Schema for user login"""
    username: str = Field(
        description="Username of the user",
        min_length=3,
        max_length=50
    )
