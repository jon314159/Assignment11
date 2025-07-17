import pytest
from pydantic import ValidationError
from app.schemas.base import UserBase, PasswordMixin, UserCreate, UserLogin


def make_user_base(**overrides):
    data = dict(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        username="johndoe",
    )
    data.update(overrides)
    return UserBase(**data)


def make_password_mixin(password):
    return PasswordMixin(password=password)


def make_user_create(**overrides):
    data = dict(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        username="johndoe",
        password="SecurePass123"
    )
    data.update(overrides)
    return UserCreate(**data)


def make_user_login(**overrides):
    data = dict(
        username="johndoe",
        password="SecurePass123"
    )
    data.update(overrides)
    return UserLogin(**data)


def test_user_base_valid():
    user = make_user_base()
    assert user.email == "john.doe@example.com"


def test_user_base_invalid_email():
    with pytest.raises(ValidationError, match="value is not a valid email address"):
        make_user_base(email="not-an-email")


def test_user_base_short_username():
    with pytest.raises(ValidationError, match="ensure this value has at least 3 characters"):
        make_user_base(username="jd")


def test_password_mixin_valid():
    pw = make_password_mixin("SecurePass123")
    assert pw.password == "SecurePass123"


@pytest.mark.parametrize("password,expected_error", [
    ("short", "ensure this value has at least 8 characters"),
    ("lowercase1", "Password must contain at least one uppercase letter"),
    ("UPPERCASE1", "Password must contain at least one lowercase letter"),
    ("NoDigitsHere", "Password must contain at least one digit"),
    ("12345678", "Password must contain at least one uppercase letter"),
])
def test_password_mixin_invalid(password, expected_error):
    with pytest.raises(ValidationError, match=expected_error):
        make_password_mixin(password)


def test_user_create_valid():
    user = make_user_create()
    assert user.username == "johndoe"


def test_user_create_invalid_password():
    with pytest.raises(ValidationError, match="Password must contain at least one digit"):
        make_user_create(password="NoDigits")


def test_user_create_extra_fields():
    with pytest.raises(ValidationError):
        make_user_create(extra_field="not allowed")


def test_user_login_valid():
    login = make_user_login()
    assert login.username == "johndoe"


def test_user_login_invalid_username():
    with pytest.raises(ValidationError, match="ensure this value has at least 3 characters"):
        make_user_login(username="jd")


def test_user_login_invalid_password():
    with pytest.raises(ValidationError, match="Password must contain at least one digit"):
        make_user_login(password="NoDigitsHere")
