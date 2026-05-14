from sqlalchemy import create_engine, event, inspect
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from pathlib import Path
import sqlite3
import sys
import logging

logger = logging.getLogger("kuechenplaner.database")


def _get_data_dir() -> Path:
    # "__compiled__" is injected into every module's globals by Nuitka.
    # In regular Python (development), it is absent.
    if "__compiled__" in globals():
        import os
        if sys.platform == "win32":
            base = Path(os.environ["APPDATA"]) / "KuechenApp"
        else:
            xdg = os.environ.get("XDG_DATA_HOME", "")
            base = (Path(xdg) if xdg else Path.home() / ".local" / "share") / "KuechenApp"
    else:
        # Development: keep data/ next to the project root
        base = Path(__file__).parent.parent / "data"
    base.mkdir(parents=True, exist_ok=True)
    return base


DATA_DIR = _get_data_dir()

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


# Baseline revision: the revision ID that represents the schema state
# after Alembic migration 001_initial_schema. Pre-Alembic databases
# (created via Base.metadata.create_all in older app versions) match this
# state and should be stamped to it instead of running the initial migration.
INITIAL_SCHEMA_REVISION = "001"


def _build_alembic_config():
    """Build an Alembic Config pointing at the bundled migrations directory."""
    from alembic.config import Config

    alembic_ini_path = Path(__file__).parent.parent / "alembic.ini"
    if not alembic_ini_path.exists():
        return None

    alembic_cfg = Config(str(alembic_ini_path))
    # Absolute path so it works regardless of CWD (e.g., Nuitka builds)
    alembic_cfg.set_main_option(
        "script_location",
        str(alembic_ini_path.parent / "alembic"),
    )
    alembic_cfg.set_main_option("sqlalchemy.url", SQLALCHEMY_DATABASE_URL)
    return alembic_cfg


def run_migrations():
    """Bring the database schema up to the latest Alembic revision.

    Three cases are handled:
    1. Fresh DB (no tables): `upgrade head` creates the full schema from migrations.
    2. Legacy DB (has tables, no `alembic_version`): the DB was originally
       created by `Base.metadata.create_all` and matches the initial schema
       snapshot. Stamp it to `INITIAL_SCHEMA_REVISION`, then upgrade forward.
    3. Tracked DB (has `alembic_version`): normal `upgrade head`.
    """
    import app.models  # noqa: F401 - ensure models are registered with Base.metadata
    try:
        from alembic import command
    except ImportError:
        logger.warning("Alembic not installed, skipping migrations")
        return

    alembic_cfg = _build_alembic_config()
    if alembic_cfg is None:
        logger.warning("alembic.ini not found, skipping migrations")
        return

    try:
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())

        if tables and "alembic_version" not in tables:
            logger.info(
                "Legacy database detected (no alembic_version table); "
                "stamping to revision %s",
                INITIAL_SCHEMA_REVISION,
            )
            command.stamp(alembic_cfg, INITIAL_SCHEMA_REVISION)

        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations completed successfully")
    except Exception as e:
        logger.error(f"Error running migrations: {e}", exc_info=True)
        raise


def backup_database() -> None:
    """Create a rotating daily backup of the SQLite DB (keeps last 7 copies)."""
    from datetime import date

    db_path = DATA_DIR / "app.db"
    if not db_path.exists():
        return

    backup_dir = DATA_DIR / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    backup_path = backup_dir / f"app_{date.today().isoformat()}.db"
    if not backup_path.exists():
        try:
            src = sqlite3.connect(str(db_path))
            dst = sqlite3.connect(str(backup_path))
            src.backup(dst)
            src.close()
            dst.close()
            logger.info(f"Database backed up to {backup_path}")
        except Exception as e:
            logger.error(f"Database backup failed: {e}", exc_info=True)

    # Keep only the last 7 daily backups
    backups = sorted(backup_dir.glob("app_*.db"))
    for old in backups[:-7]:
        try:
            old.unlink()
            logger.info(f"Removed old backup: {old.name}")
        except OSError as e:
            logger.warning(f"Could not remove old backup {old.name}: {e}")
