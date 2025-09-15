import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/node_llm_system")

# Create engine
engine = create_engine(
    DATABASE_URL,
    poolclass=StaticPool,
    echo=False  # Set to True for SQL query logging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 