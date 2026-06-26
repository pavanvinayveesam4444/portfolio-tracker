"""
Database service.
Handles PostgreSQL connection and session management.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Base
from config import DATABASE_URL
import logging

logger = logging.getLogger(__name__)


# Create engine — connects Python to PostgreSQL
engine = create_engine(DATABASE_URL, echo=False)

# Create session factory
SessionLocal = sessionmaker(bind=engine)


def create_tables() -> None:
    """
    Create all tables in PostgreSQL.
    Reads all models that inherit from Base
    and creates their tables automatically.
    """
    Base.metadata.create_all(engine)
    logger.info("All tables created successfully")


def get_session() -> Session:
    """
    Get a database session.
    Use this to interact with the database.
    """
    return SessionLocal()


def close_session(session: Session) -> None:
    """
    Close the database session.
    Always close when done.
    """
    session.close()
    logger.info("Database session closed")