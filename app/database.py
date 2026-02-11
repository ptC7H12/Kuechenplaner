from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from pathlib import Path
import logging

logger = logging.getLogger("kuechenplaner.database")

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


# Enable WAL mode for better concurrency with SQLite
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Base class for all models
class Base(DeclarativeBase):
    pass


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Create all tables
def create_tables():
    import app.models  # noqa: F401 - ensure models are registered with Base.metadata
    Base.metadata.create_all(bind=engine)


# Run database migrations
def run_migrations():
    """Run pending Alembic migrations"""
    try:
        from alembic.config import Config
        from alembic import command

        # Get the alembic.ini path
        alembic_ini_path = Path(__file__).parent.parent / "alembic.ini"

        if not alembic_ini_path.exists():
            logger.warning("alembic.ini not found, skipping migrations")
            return

        # Create Alembic config
        alembic_cfg = Config(str(alembic_ini_path))

        # Run migrations to the latest version
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations completed successfully")
    except Exception as e:
        logger.error(f"Error running migrations: {e}", exc_info=True)
