import pytest
import importlib
import sys
from unittest.mock import patch
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from app.schemas.enums import CalculationType  # clean import

DATABASE_MODULE = "app.database"


@pytest.fixture
def mock_settings(monkeypatch):
    """Mock settings.DATABASE_URL before app.database is imported."""
    mock_url = "postgresql://user:password@localhost:5432/test_db"
    from unittest.mock import MagicMock
    mock_settings = MagicMock()
    mock_settings.DATABASE_URL = mock_url

    # Clear app.database from sys.modules so patch applies on re-import
    sys.modules.pop(DATABASE_MODULE, None)

    # Inject mocked settings into app.database
    monkeypatch.setitem(sys.modules, f"{DATABASE_MODULE}.settings", mock_settings)

    return mock_settings


def reload_database_module():
    """Reload the app.database module after patching."""
    sys.modules.pop(DATABASE_MODULE, None)
    return importlib.import_module(DATABASE_MODULE)


def test_base_is_declarative(mock_settings):
    db = reload_database_module()
    assert hasattr(db.Base, "metadata")


def test_get_engine_success(mock_settings):
    db = reload_database_module()
    engine = db.get_engine()
    assert isinstance(engine, Engine)


def test_get_sessionmaker_success(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")
    sys.modules.pop(DATABASE_MODULE, None)
    db = importlib.import_module(DATABASE_MODULE)
    engine = db.get_engine()
    SessionLocal = db.get_sessionmaker(engine)
    assert isinstance(engine, Engine)
    assert isinstance(SessionLocal, sessionmaker)


def test_get_engine_logs_and_raises_error(capfd, monkeypatch):
    """Test that get_engine logs and raises error when create_engine fails."""

    # Patch create_engine to raise error BEFORE importing app.database
    with patch("sqlalchemy.create_engine", side_effect=SQLAlchemyError("Mocked engine error")):

        # Patch settings with a dummy value
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
        sys.modules.pop(DATABASE_MODULE, None)

        # Now import the database module (get_engine will raise on import)
        with pytest.raises(SQLAlchemyError, match="Mocked engine error"):
            importlib.import_module(DATABASE_MODULE).get_engine()

        out, _ = capfd.readouterr()
        assert "Error creating engine: Mocked engine error" in out
