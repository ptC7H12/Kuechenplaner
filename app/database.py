from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from pathlib import Path

# Create data directory if it doesn't exist
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# Database URL
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DATA_DIR}/app.db"

# Create engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    echo=False  # Set to True for SQL debugging
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create all tables
def create_tables():
    from app.models import Base
    Base.metadata.create_all(bind=engine)

# Run database migrations
def run_migrations():
    """Run pending Alembic migrations"""
    try:
        from alembic.config import Config
        from alembic import command
        import os

        # Get the alembic.ini path
        alembic_ini_path = Path(__file__).parent.parent / "alembic.ini"

        if not alembic_ini_path.exists():
            print("alembic.ini not found, skipping migrations")
            return

        # Create Alembic config
        alembic_cfg = Config(str(alembic_ini_path))

        # Run migrations to the latest version
        command.upgrade(alembic_cfg, "head")
        print("Database migrations completed successfully")
    except Exception as e:
        print(f"Error running migrations: {e}")
        # Don't fail the application if migrations fail
        pass