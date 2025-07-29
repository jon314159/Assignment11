import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from tests.conftest import create_fake_user, managed_db_session
from app.models.calculation import Calculation


def test_database_connection(db_session):
    assert db_session.execute(text("SELECT 1")).scalar() == 1


def test_managed_session_rollback():
    with managed_db_session() as session:
        session.execute(text("SELECT 1"))
        with pytest.raises(Exception, match="nonexistent_table"):
            session.execute(text("SELECT * FROM nonexistent_table"))


def test_create_user_with_faker(db_session):
    user_data = create_fake_user()
    password = user_data.pop("password")
    user = User(**user_data, hashed_password=User.hash_password(password))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.id is not None
    assert user.email == user_data["email"]


def test_create_multiple_users(db_session):
    users = []
    for _ in range(3):
        data = create_fake_user()
        password = data.pop("password")
        users.append(User(**data, hashed_password=User.hash_password(password)))
    db_session.add_all(users)
    db_session.commit()

    emails = [u.email for u in users]
    usernames = [u.username for u in users]

    db_users = db_session.query(User).all()
    db_emails = {u.email for u in db_users}
    db_usernames = {u.username for u in db_users}

    assert all(email in db_emails for email in emails)
    assert all(username in db_usernames for username in usernames)


@pytest.mark.parametrize("field, val", [
    ("email", "unique_email_test@example.com"),
    ("username", "unique_user_test")
])
def test_unique_constraints(db_session, field, val):
    user1_data = create_fake_user()
    user2_data = create_fake_user()

    user1_data[field] = val
    user2_data[field] = val

    password1 = user1_data.pop("password")
    user1 = User(**user1_data, hashed_password=User.hash_password(password1))
    db_session.add(user1)
    db_session.commit()

    password2 = user2_data.pop("password")
    user2 = User(**user2_data, hashed_password=User.hash_password(password2))
    db_session.add(user2)

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_transaction_rollback(db_session):
    count_before = db_session.query(User).count()
    data = create_fake_user()
    password = data.pop("password")
    user = User(**data, hashed_password=User.hash_password(password))
    db_session.add(user)

    with pytest.raises(Exception):
        db_session.execute(text("SELECT * FROM nonexistent_table"))
        db_session.commit()

    db_session.rollback()
    assert db_session.query(User).count() == count_before


def test_persistence_after_constraint(db_session):
    u1_data = create_fake_user()
    u2_data = create_fake_user()

    u1_data["email"] = "jane.doe@example.com"
    u1_data["username"] = "janedoe"
    u1_password = u1_data.pop("password")

    u1 = User(**u1_data, hashed_password=User.hash_password(u1_password))
    db_session.add(u1)
    db_session.commit()

    u2_data["email"] = u1.email
    u2_password = u2_data.pop("password")

    u2 = User(**u2_data, hashed_password=User.hash_password(u2_password))
    db_session.add(u2)

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    found = db_session.query(User).filter_by(id=u1.id).first()
    assert found is not None
    assert found.email == u1.email
    assert found.username == u1.username


def test_session_handling(db_session):
    # CLEANUP: reset users table — only for this test
    db_session.query(User).delete()
    db_session.commit()

    assert db_session.query(User).count() == 0

    u1 = User(
        first_name="Alice", last_name="Smith", email="alice.smith@example.com",
        username="alice_smith", hashed_password=User.hash_password("Alice123!")
    )
    db_session.add(u1)
    db_session.commit()
    assert db_session.query(User).count() == 1

    u2 = User(
        first_name="Bob", last_name="Brown", email=u1.email,
        username="bob_brown", hashed_password=User.hash_password("Bob456!")
    )
    db_session.add(u2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    u3 = User(
        first_name="Charlie", last_name="Johnson", email="charlie.johnson@example.com",
        username="charlie_j", hashed_password=User.hash_password("Charlie789!")
    )
    db_session.add(u3)
    db_session.commit()

    emails = {u.email for u in db_session.query(User).all()}
    assert len(emails) == 2
    assert "alice.smith@example.com" in emails
    assert "charlie.johnson@example.com" in emails


def test_error_handling():
    with pytest.raises(Exception, match="INVALID SQL"):
        with managed_db_session() as session:
            session.execute(text("INVALID SQL"))

