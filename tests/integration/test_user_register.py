from sys import exc_info
import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from tests.conftest import create_fake_user
import uuid


def test_register_happy_path(db_session):
    user_data = create_fake_user()
    user = User.register(db_session, user_data.copy())

    # Refresh from DB to get fully populated object
    db_session.refresh(user)

    assert user.id is not None
    assert user.email == user_data['email']
    assert user.username == user_data['username']
    assert user.hashed_password != user_data['password']

    created_at: datetime = user.created_at
    assert isinstance(created_at, datetime)

    # Ensure it's timezone-aware
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)

    # Allow created_at to be within ±5 minutes of now
    lower_bound = now - timedelta(minutes=5)
    upper_bound = now + timedelta(minutes=5)

    assert lower_bound <= created_at <= upper_bound, \
        f"created_at {created_at} not within {lower_bound} - {upper_bound}"


def test_register_short_password(db_session):
    user_data = create_fake_user()
    user_data['password'] = 'short'

    with pytest.raises(ValueError, match="Password must be at least 8 characters long"):
        User.register(db_session, user_data)


def test_register_long_password(db_session):
    user_data = create_fake_user()
    user_data['password'] = 'a' * 129

    with pytest.raises(ValueError, match="Password must not exceed 128 characters"):
        User.register(db_session, user_data)


def test_register_duplicate_username(db_session):
    user_data = create_fake_user()

    # First registration
    User.register(db_session, user_data.copy())

    # Change email so only username conflicts
    user_data['email'] = f"other_{user_data['email']}"

    with pytest.raises(ValueError, match="Username or email already exists"):
        User.register(db_session, user_data)


def test_register_duplicate_email(db_session):
    user_data = create_fake_user()

    # First registration
    User.register(db_session, user_data.copy())

    # Change username so only email conflicts
    user_data['username'] = f"{user_data['username']}_2"

    with pytest.raises(ValueError):
        User.register(db_session, user_data)

        


def test_register_invalid_user_data(db_session):
    user_data = create_fake_user()
    user_data['email'] = 'not-an-email'

    with pytest.raises(ValueError, match="Validation error"):
        User.register(db_session, user_data)

def test_register_password_requires_special_character(db_session):
    user_data = create_fake_user()
    user_data['password'] = 'Password123'  # missing special char

    with pytest.raises(ValueError, match="Password must contain at least one special character"):
        User.register(db_session, user_data)

def test_register_password_none_provided(db_session):
    user_data = create_fake_user()
    user_data['password'] = None  # explicitly None

    with pytest.raises(ValueError, match="Password must be provided"):
        User.register(db_session, user_data)

def test_authenticate_happy_path(db_session):
    user_data = create_fake_user()
    password = user_data['password']
    user = User.register(db_session, user_data.copy())

    result = User.authenticate(db_session, user.username, password)

    assert result is not None
    assert isinstance(result, dict)
    assert "access_token" in result
    assert "user" in result
    assert result["user"]["email"] == user.email


def test_authenticate_wrong_password(db_session):
    user_data = create_fake_user()
    User.register(db_session, user_data.copy())

    result = User.authenticate(db_session, user_data['username'], "WrongPassword123!")
    assert result is None


def test_authenticate_unknown_user(db_session):
    result = User.authenticate(db_session, "nonexistent_user", "SomePassword123!")
    assert result is None


def test_authenticate_with_email(db_session):
    user_data = create_fake_user()
    password = user_data['password']
    user = User.register(db_session, user_data.copy())

    result = User.authenticate(db_session, user.email, password)

    assert result is not None
    assert "access_token" in result
    assert result["user"]["email"] == user.email

from datetime import timezone

def test_update_last_login(db_session):
    user_data = create_fake_user()
    user = User.register(db_session, user_data.copy())

    db_session.refresh(user)
    print(f"Before update: last_login={user.last_login}")
    assert user.last_login is None

    user.update_last_login(db_session)

    db_session.refresh(user)
    print(f"After update: last_login={user.last_login}")

    assert user.last_login is not None, "last_login is still None after update"
    assert isinstance(user.last_login, datetime)

    # Convert to aware if naive (test dbs often return naive)
    if user.last_login.tzinfo is None:
        user_last_login_aware = user.last_login.replace(tzinfo=timezone.utc)
    else:
        user_last_login_aware = user.last_login

    now = datetime.now(timezone.utc)
    assert now - timedelta(minutes=5) <= user_last_login_aware <= now + timedelta(minutes=5), \
        f"last_login {user_last_login_aware} not within expected range"

def test_get_user_by_id_valid(db_session):
    user_data = create_fake_user()
    user = User.register(db_session, user_data.copy())

    fetched = User.get_user_by_id(db_session, str(user.id))
    assert fetched is not None
    assert fetched.id == user.id
    assert fetched.email == user.email


def test_get_user_by_id_invalid_uuid(db_session):
    result = User.get_user_by_id(db_session, "not-a-valid-uuid")
    assert result is None


def test_get_user_by_id_nonexistent_uuid(db_session):
    random_uuid = str(uuid.uuid4())
    result = User.get_user_by_id(db_session, random_uuid)
    assert result is None

def test_register_integrity_error_via_register(db_session):
    user_data = create_fake_user()

    # first registration
    User.register(db_session, user_data.copy())

    # second registration with same username/email
    with pytest.raises(ValueError, match="Username or email already exists"):
        User.register(db_session, user_data.copy())

def test_verify_token_valid():
    # simulate a payload and create a token
    payload = {"sub": "test-user-id"}
    token = User.create_access_token(payload)

    # now verify it
    verified = User.verify_token(token)

    assert verified is not None
    assert isinstance(verified, dict)
    assert verified.get("sub") == "test-user-id"

def test_verify_token_invalid():
    # clearly invalid token
    invalid_token = "this.is.not.a.valid.token"

    verified = User.verify_token(invalid_token)

    assert verified is None




