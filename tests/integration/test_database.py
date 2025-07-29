import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine
import importlib
import sys
from app.schemas.enums import CalculationType  # now clean, no model linkage
DATABASE_MODULE = "app.database"


@pytest.fixture
def mock_settings(monkeypatch):
    """
    Fixture to mock settings.DATABASE_URL before app.database is imported.
    Ensures a test-safe DB URL is injected.
    """
    mock_url = "postgresql://user:password@localhost:5432/test_db"
    mock_settings = MagicMock()
    mock_settings.DATABASE_URL = mock_url

    # Unload app.database if already imported
    sys.modules.pop(DATABASE_MODULE, None)

    # Patch settings before module is imported
    monkeypatch.setitem(sys.modules, f"{DATABASE_MODULE}.settings", mock_settings)

    return mock_settings


def reload_database_module():
    """
    Helper to reload app.database after monkeypatching settings.
    """
    sys.modules.pop(DATABASE_MODULE, None)
    return importlib.import_module(DATABASE_MODULE)


def test_base_is_declarative(mock_settings):
    """Verify Base is a declarative_base instance."""
    db = reload_database_module()
    Base = db.Base
    assert hasattr(Base, "metadata")


def test_get_engine_success(mock_settings):
    """get_engine should return a valid SQLAlchemy Engine."""
    db = reload_database_module()
    engine = db.get_engine()
    assert isinstance(engine, Engine)


def test_get_engine_failure(monkeypatch):
    """Simulate create_engine raising SQLAlchemyError."""
    import sys
    import importlib

    # Patch sqlalchemy.create_engine BEFORE importing app.database
    from sqlalchemy import create_engine as real_create_engine
    monkeypatch.setattr("sqlalchemy.create_engine", lambda *args, **kwargs: (_ for _ in ()).throw(SQLAlchemyError("Engine error")))

    # Force reload of app.database
    sys.modules.pop("app.database", None)
    db = importlib.import_module("app.database")

    # Now call get_engine, expecting the error
    with pytest.raises(SQLAlchemyError, match="Engine error"):
        db.get_engine()



def test_get_sessionmaker_success(monkeypatch):
    """get_sessionmaker should return a valid sessionmaker bound to engine."""
    from sqlalchemy.engine import Engine
    import sys
    import importlib

    # Patch settings.DATABASE_URL
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")

    # Unload module so it reads fresh settings
    sys.modules.pop("app.database", None)
    db = importlib.import_module("app.database")

    engine = db.get_engine()
    SessionLocal = db.get_sessionmaker(engine)

    assert isinstance(engine, Engine)
    assert isinstance(SessionLocal, sessionmaker)