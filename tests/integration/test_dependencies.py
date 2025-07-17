import pytest
from unittest.mock import MagicMock, patch, ANY
from fastapi import HTTPException, status
from uuid import uuid4
from datetime import datetime

from app.auth.dependencies import get_current_user
from app.schemas.user import UserResponse
from app.models.user import User

# Sample test users
SAMPLE_USER = User(
    id=uuid4(),
    username="testuser",
    email="test@example.com",
    first_name="Test",
    last_name="User",
    is_verified=True,
    created_at=datetime.utcnow(),
    updated_at=datetime.utcnow()
)



@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def mock_verify_token():
    with patch.object(User, "verify_token") as mock:
        yield mock


def test_get_current_user_valid(mock_db, mock_verify_token):
    """Valid token and existing user."""
    mock_verify_token.return_value = SAMPLE_USER.id
    mock_db.query.return_value.filter.return_value.first.return_value = SAMPLE_USER

    user = get_current_user(db=mock_db, token="validtoken")

    assert isinstance(user, UserResponse)
    assert user.id == SAMPLE_USER.id
    assert user.username == SAMPLE_USER.username
    assert user.email == SAMPLE_USER.email
    assert user.is_verified is True

    mock_verify_token.assert_called_once_with("validtoken")
    mock_db.query.assert_called_once_with(User)
    mock_db.query.return_value.filter.assert_called_once_with(ANY)
    mock_db.query.return_value.filter.return_value.first.assert_called_once()


def test_get_current_user_invalid_token(mock_db, mock_verify_token):
    """Invalid token: no user ID returned."""
    mock_verify_token.return_value = None

    with pytest.raises(HTTPException) as exc:
        get_current_user(db=mock_db, token="invalidtoken")

    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc.value.detail == "Could not validate credentials"

    mock_verify_token.assert_called_once_with("invalidtoken")
    mock_db.query.assert_not_called()


def test_get_current_user_nonexistent_user(mock_db, mock_verify_token):
    """Valid token, but no user found in DB."""
    mock_verify_token.return_value = SAMPLE_USER.id
    mock_db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc:
        get_current_user(db=mock_db, token="validtoken")

    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc.value.detail == "Could not validate credentials"

    mock_verify_token.assert_called_once_with("validtoken")
    mock_db.query.assert_called_once_with(User)
    mock_db.query.return_value.filter.assert_called_once_with(ANY)
    mock_db.query.return_value.filter.return_value.first.assert_called_once()


