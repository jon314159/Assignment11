from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict

class UserResponse(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: EmailStr
    username: str
    is_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    class Config:
        orm_mode = True 

class Token(BaseModel):
    """Scema for authentication token"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "access_token": "example_token",
                "token_type": "bearer",
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "first_name": "John",
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john.doe@example.com",
                    "username": "johndoe",
                    "created_at": "2023-10-01T12:00:00Z",
                    "is_verified": True,
                    "updated_at": "2023-10-01T12:00:00Z"
                }
            }
        }    
    )

class TokenData(BaseModel):
    """Schema for token data"""
    id: Optional[UUID] = None

class UserLogin(BaseModel):
    """Schema for user login"""
    username: str
    password: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "johndoe",
                "password": "securepassword123"
            }
        }
    )
