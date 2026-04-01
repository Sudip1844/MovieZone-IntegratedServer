
# IntegratedServer/database/connection.py
# Database connection and session management

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator
import logging
from config import DATABASE_URL

logger = logging.getLogger(__name__)

# Create engine
try:
    engine = create_engine(
        DATABASE_URL,
        echo=False,  # Set to True for SQL debugging
        pool_pre_ping=True,  # Test connections before using
        pool_recycle=3600,  # Recycle connections every hour
    )
    logger.info("✅ Database engine created successfully")
except Exception as e:
    logger.error(f"❌ Failed to create database engine: {e}")
    engine = None

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager for database sessions"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()

def init_db():
    """Initialize database (create all tables)"""
    if engine is None:
        logger.error("❌ Cannot initialize database: engine not created")
        return False
    
    try:
        from database.models import Base
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables initialized")
        return True
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return False

def get_db():
    """Dependency for Flask endpoints"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
