from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError
from .config import settings

def  get_engine(database_url: str = settings.DATABASE_URL):
    """Create and return a SQLAlchemy engine."""
    try:
        engine = create_engine(settings.DATABASE_URL, echo=True)
        return engine
    except SQLAlchemyError as e:
        print(f"Error creating engine: {e}")
        raise

def get_sessionmaker(engine):
    """Create and return a sessionmaker bound to the engine."""
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)

engine = get_engine()
SessionLocal = get_sessionmaker(engine)
Base = declarative_base()

def get_db(): #pragma: no cover
    """Dependency to get a database session."""
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Database error: {e}")
        raise
    finally:
        db.close()