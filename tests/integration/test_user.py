import pytest
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, clear_mappers, Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from jose import jwt, JWTError
from datetime import timedelta, datetime, timezone
from uuid import UUID
from unittest.mock import patch
from typing import Generator
from contextlib import contextmanager

from app.models.user import User, Base, SECRET_KEY, ALGORITHM
from tests.conftest import create_fake_user


@contextmanager
def managed_db_session() -> Generator[Session, None, None]:
    """
    Context manager to handle database sessions for testing.
    """
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)

    db_session = SessionLocal()
    try:
        yield db_session
    except SQLAlchemyError as e:
        db_session.rollback()
        logging.error(f"Database error: {e}")
        raise
    finally:
        db_session.close()


@pytest.fixture(scope="session")
def faker():
    from faker import Faker
    return Faker()


class TestUserModel:
    """Test suite for User model."""

    @pytest.fixture
    def db_session(self):
        with managed_db_session() as session:
            yield session

    @pytest.fixture
    def fake_user_data(self, faker):
        return create_fake_user()

    @pytest.fixture
    def created_user(self, db_session, fake_user_data):
        user = User.register(db_session, fake_user_data.copy())
        return user

    def test_user_model_creation(self, fake_user_data):
        user = User(
            first_name=fake_user_data["first_name"],
            last_name=fake_user_data["last_name"],
            email=fake_user_data["email"],
            username=fake_user_data["username"],
            hashed_password=User.hash_password(fake_user_data["password"])
        )
        assert user.first_name == fake_user_data["first_name"]
        assert user.last_name == fake_user_data["last_name"]
        assert user.email == fake_user_data["email"]
        assert user.username == fake_user_data["username"]
        assert user.hashed_password != fake_user_data["password"]
        assert user.is_verified is False
        assert user.last_login is None

    def test_user_repr(self, created_user):
        repr_str = repr(created_user)
        assert "User(" in repr_str
        assert f"id={created_user.id}" in repr_str
        assert f"username={created_user.username}" in repr_str
        assert f"email={created_user.email}" in repr_str

    def test_hash_password(self, faker):
        password = faker.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True)
        hashed = User.hash_password(password)
        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")

    def test_verify_password_valid(self, created_user, fake_user_data):
        assert created_user.verify_password(fake_user_data["password"]) is True

    def test_verify_password_invalid(self, created_user, faker):
        wrong_password = faker.password(length=10)
        assert created_user.verify_password(wrong_password) is False

    def test_verify_password_invalid_type(self):
        user = User()
        with patch.object(user, 'hashed_password', new=None):
            with pytest.raises(TypeError, match="Invalid hashed_password type"):
                user.verify_password("password")

    def test_create_access_token_default_expiry(self, faker):
        user_id = str(faker.uuid4())
        data = {"sub": user_id}
        token = User.create_access_token(data)
        assert isinstance(token, str)

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == user_id
        assert "exp" in payload

    def test_create_access_token_custom_expiry(self, faker):
        user_id = str(faker.uuid4())
        data = {"sub": user_id}
        custom_delta = timedelta(hours=1)
        token = User.create_access_token(data, custom_delta)

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == user_id

        exp_time = datetime.fromtimestamp(payload["exp"], timezone.utc)
        expected_time = datetime.now(timezone.utc) + custom_delta
        assert abs((exp_time - expected_time).total_seconds()) < 10

    def test_register_success(self, db_session, fake_user_data):
        user = User.register(db_session, fake_user_data)
        assert user.first_name == fake_user_data["first_name"]
        assert user.last_name == fake_user_data["last_name"]
        assert user.email == fake_user_data["email"]
        assert user.username == fake_user_data["username"]
        assert user.hashed_password != fake_user_data["password"]
        assert user.is_verified is False
        assert user.created_at is not None
        assert isinstance(user.id, UUID)

    def test_register_password_too_short(self, db_session, fake_user_data):
        fake_user_data["password"] = "short"
        with pytest.raises(ValueError, match="Password must be at least 8 characters long"):
            User.register(db_session, fake_user_data)

    def test_register_password_too_long(self, db_session, fake_user_data):
        fake_user_data["password"] = "a" * 129
        with pytest.raises(ValueError, match="Password must not exceed 128 characters"):
            User.register(db_session, fake_user_data)

    def test_register_duplicate_username(self, db_session, fake_user_data):
        User.register(db_session, fake_user_data.copy())
        duplicate_data = create_fake_user()
        duplicate_data["username"] = fake_user_data["username"]
        with pytest.raises(ValueError, match="Username or email already exists"):
            User.register(db_session, duplicate_data)

    def test_register_duplicate_email(self, db_session, fake_user_data):
        User.register(db_session, fake_user_data.copy())
        duplicate_data = create_fake_user()
        duplicate_data["email"] = fake_user_data["email"]
        with pytest.raises(ValueError, match="Username or email already exists"):
            User.register(db_session, duplicate_data)

    def test_register_validation_error(self, db_session, fake_user_data):
        fake_user_data.pop("first_name")
        with pytest.raises(ValueError, match="Validation error"):
            User.register(db_session, fake_user_data)

    def test_register_integrity_error(self, db_session, fake_user_data):
        User.register(db_session, fake_user_data.copy())
        dummy_exc = Exception("orig")
        with patch.object(db_session, 'commit', side_effect=IntegrityError("stmt", "params", dummy_exc)):
            with pytest.raises(ValueError, match="User already exists"):
                User.register(db_session, fake_user_data)

    def test_register_generic_exception(self, db_session, fake_user_data):
        with patch.object(db_session, 'add', side_effect=Exception("DB failed")):
            with pytest.raises(ValueError, match="Registration failed"):
                User.register(db_session, fake_user_data)

    def test_authenticate_success_with_username(self, db_session, created_user, fake_user_data):
        result = User.authenticate(db_session, fake_user_data["username"], fake_user_data["password"])
        assert result is not None
        assert result["access_token"]
        assert result["token_type"] == "bearer"
        assert result["user"]["username"] == fake_user_data["username"]

    def test_authenticate_invalid_user(self, db_session, faker):
        result = User.authenticate(db_session, faker.user_name(), faker.password())
        assert result is None

    def test_verify_token_valid(self, faker):
        user_id = str(faker.uuid4())
        data = {"sub": user_id, "exp": datetime.now(timezone.utc) + timedelta(hours=1)}
        token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

        payload = User.verify_token(token)
        assert payload is not None
        assert payload["sub"] == user_id

    def test_verify_token_invalid(self):
        invalid_token = "invalid.token.here"
        payload = User.verify_token(invalid_token)
        assert payload is None

    def test_get_user_by_id_success(self, db_session, created_user):
        user = User.get_user_by_id(db_session, str(created_user.id))
        assert user is not None
        assert user.id == created_user.id

    def test_get_user_by_id_not_found(self, db_session, faker):
        user = User.get_user_by_id(db_session, str(faker.uuid4()))
        assert user is None

    def test_to_dict(self, created_user):
        user_dict = created_user.to_dict()
        assert "hashed_password" not in user_dict
        assert user_dict["id"] == str(created_user.id)


class TestUserModelIntegration:
    """Integration tests for User model."""

    @pytest.fixture
    def db_session(self):
        with managed_db_session() as session:
            yield session

    def test_complete_user_workflow(self, db_session):
        user_data = create_fake_user()
        user = User.register(db_session, user_data)
        assert user.id is not None

        auth_result = User.authenticate(db_session, user_data["username"], user_data["password"])
        assert auth_result is not None

        token = auth_result["access_token"]
        payload = User.verify_token(token)
        assert payload is not None

        retrieved_user = User.get_user_by_id(db_session, payload["sub"])
        assert retrieved_user is not None
        assert str(retrieved_user.username) == user_data["username"]


class TestUserModelEdgeCases:
    """Edge case tests for User model."""

    @pytest.fixture
    def db_session(self):
        with managed_db_session() as session:
            yield session

    def test_empty_string_values(self, db_session):
        user_data = create_fake_user()
        user_data["first_name"] = ""
        with pytest.raises(ValueError):
            User.register(db_session, user_data)

    def test_unicode_characters(self, db_session):
        user_data = create_fake_user()
        user_data["first_name"] = "José"
        user_data["last_name"] = "García"
        user = User.register(db_session, user_data)
        assert str(user.first_name) == "José"
        assert str(user.last_name) == "García"

    def test_very_long_valid_password(self, db_session):
        user_data = create_fake_user()
        user_data["password"] = "a" * 128
        user = User.register(db_session, user_data)
        assert user.verify_password("a" * 128)


@pytest.fixture(scope="function", autouse=True)
def clear_sqlalchemy_mappers():
    yield
    clear_mappers()
