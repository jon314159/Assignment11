import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from tests.conftest import create_fake_user, managed_db_session


# ======================================================================================
# Connection & Session Tests
# ======================================================================================

def test_database_connection(db_session):
    assert db_session.execute(text("SELECT 1")).scalar() == 1



def test_managed_session_rollback():
    with managed_db_session() as session:
        session.execute(text("SELECT 1"))
        with pytest.raises(Exception, match="nonexistent_table"):
            session.execute(text("SELECT * FROM nonexistent_table"))


# ======================================================================================
# User Creation Tests
# ======================================================================================

def test_create_user_with_faker(db_session):
    user_data = create_fake_user()
    user = User(**user_data)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.id is not None
    assert user.email == user_data["email"]


def test_create_multiple_users(db_session):
    users = [User(**create_fake_user()) for _ in range(3)]
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

    db_session.add(User(**user1_data))
    db_session.commit()

    db_session.add(User(**user2_data))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


# ======================================================================================
# Transaction Tests
# ======================================================================================

def test_transaction_rollback(db_session):
    count_before = db_session.query(User).count()
    user = User(**create_fake_user())
    db_session.add(user)

    with pytest.raises(Exception):
        db_session.execute(text("SELECT * FROM nonexistent_table"))
        db_session.commit()

    db_session.rollback()
    assert db_session.query(User).count() == count_before


def test_persistence_after_constraint(db_session):
    u1_data = {
        "first_name": "Jane", "last_name": "Doe", "email": "jane.doe@example.com",
        "username": "janedoe", "password": "SecurePass123!"
    }
    u1 = User(**u1_data)
    db_session.add(u1)
    db_session.commit()

    u2_data = {
        "first_name": "John", "last_name": "Smith", "email": u1.email,
        "username": "johnsmith", "password": "AnotherPass456!"
    }
    u2 = User(**u2_data)
    db_session.add(u2)

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    found = db_session.query(User).filter_by(id=u1.id).first()
    assert found is not None
    assert found.email == u1.email
    assert found.username == u1.username


# ======================================================================================
# Query & Update Tests
# ======================================================================================

def test_query_methods(db_session, seed_users):
    assert db_session.query(User).count() >= len(seed_users)

    first_user = seed_users[0]
    assert db_session.query(User).filter_by(email=first_user.email).first() is not None

    users_by_email = db_session.query(User).order_by(User.email).all()
    assert len(users_by_email) >= len(seed_users)


def test_update_with_refresh(db_session, test_user):
    new_email = f"updated_{test_user.email}"
    old_updated_at = test_user.updated_at

    test_user.email = new_email
    db_session.commit()
    db_session.refresh(test_user)

    assert test_user.email == new_email
    assert test_user.updated_at > old_updated_at


@pytest.mark.slow
def test_bulk_operations(db_session):
    users = [User(**create_fake_user()) for _ in range(10)]
    db_session.bulk_save_objects(users)
    db_session.commit()

    count = db_session.query(User).count()
    assert count >= 10


def test_session_handling(db_session):
    assert db_session.query(User).count() == 0

    u1 = User(
        first_name="Alice", last_name="Smith", email="alice.smith@example.com",
        username="alice_smith", password="Alice123!"
    )
    db_session.add(u1)
    db_session.commit()
    assert db_session.query(User).count() == 1

    u2 = User(
        first_name="Bob", last_name="Brown", email=u1.email,
        username="bob_brown", password="Bob456!"
    )
    db_session.add(u2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    u3 = User(
        first_name="Charlie", last_name="Johnson", email="charlie.johnson@example.com",
        username="charlie_j", password="Charlie789!"
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
