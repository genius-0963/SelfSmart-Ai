"""
Database connection and session management
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Database URL from environment or default to SQLite for development
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost:5432/smartshelf"
)

# Create engine
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=os.getenv("DEBUG", "false").lower() == "true"
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=os.getenv("DEBUG", "false").lower() == "true"
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """
    Dependency to get database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def init_db():
    """
    Initialize database tables
    """
    # Import all models to ensure they are registered
    from .models import User, ChatSession, Message, Product, AnalyticsEvent, UserPreference
    
    # Create all tables
    Base.metadata.create_all(bind=engine)


async def close_db():
    """
    Close database connections
    """
    engine.dispose()
