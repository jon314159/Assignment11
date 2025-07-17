import pytest
from pydantic import ValidationError
from app.schemas.base import UserBase, PasswordMixin, UserCreate, UserLogin


def test_user_base_valid():
    user = UserBase(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        username="johndoe"
    )
    assert user.email == "john.doe@example.com"


def test_user_base_invalid_email():
    with pytest.raises(ValidationError, match="value is not a valid email address"):
        UserBase(
            first_name="John",
            last_name="Doe",
            email="not-an-email",
            username="johndoe"
        )


def test_user_base_short_username():
    with pytest.raises(ValidationError):
        UserBase(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            username="jd"
        )
    

def test_password_mixin_valid():
    pw = PasswordMixin(password="SecurePass123!")
    assert pw.password == "SecurePass123!"


@pytest.mark.parametrize("password, expected_msg", [
    ("short", "Password must be at least 8 characters long"),
    ("lowercase1", "Password must contain at least one uppercase letter"),
    ("UPPERCASE1", "Password must contain at least one lowercase letter"),
    ("12345678", "Password must contain at least one uppercase letter"),
])
def test_password_mixin_invalid(password, expected_msg):
    with pytest.raises(ValidationError, match=expected_msg):
        PasswordMixin(password=password)


def test_user_create_valid():
    user = UserCreate(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        username="johndoe",
        password="SecurePass123!"
    )
    assert user.username == "johndoe"


def test_user_create_invalid_password():
    with pytest.raises(ValidationError, match="Password must contain at least one digit"):
        UserCreate(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            username="johndoe",
            password="NoDigitsHere!"
        )


def test_user_login_valid():
    login = UserLogin(
        username="johndoe",
        password="SecurePass123!"
    )
    assert login.username == "johndoe"



def test_user_login_invalid_username():
    with pytest.raises(ValidationError):
        UserLogin(
            username="jd",
            password="SecurePass123!"
        )

def test_user_login_invalid_password():
    with pytest.raises(ValidationError, match="Password must contain at least one digit"):
        UserLogin(
            username="johndoe",
            password="NoDigitsHere!"
        )
