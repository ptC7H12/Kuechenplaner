import logging
import os
import sqlite3
import sys
from pathlib import Path

from sqlalchemy import create_engine, event, inspect
from sqlalchemy.orm import DeclarativeBase, sessionmaker

logger = logging.getLogger("kuechenplaner.database")


def _get_data_dir() -> Path:
    # "__compiled__" is injected into every module's globals by Nuitka.
    # In regular Python (development), it is absent.
    if "__compiled__" in globals():
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
    echo=False,  # Set to True for SQL debugging
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
                "Legacy database detected (no alembic_version table); stamping to revision %s",
                INITIAL_SCHEMA_REVISION,
            )
            command.stamp(alembic_cfg, INITIAL_SCHEMA_REVISION)

        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations completed successfully")
    except Exception as e:
        logger.error(f"Error running migrations: {e}", exc_info=True)
        raise


BACKUP_DIR = DATA_DIR / "backups"

# Triggers whose backups are protected from auto-cleanup. Auto-backups outside
# this set are pruned to keep at most 7 entries.
_PROTECTED_TRIGGERS = ("manual", "pre-restore", "pre-reset")


def _is_protected_backup(path: Path) -> bool:
    return any(path.stem.endswith(f"_{t}") for t in _PROTECTED_TRIGGERS)


def backup_database(trigger: str = "auto") -> Path | None:
    """Create a backup of the SQLite DB and return the resulting path.

    - ``trigger="auto"`` only creates a new file if no auto-backup exists for
      today (`app_YYYY-MM-DD_*_auto.db`); cleanup keeps the last 7 auto-backups.
    - ``trigger="manual"`` always creates a new file (timestamp gives uniqueness)
      and is never cleaned up.
    - ``trigger="pre-restore"`` / ``"pre-reset"`` are safety snapshots taken
      immediately before destructive operations; never cleaned up.

    Returns the path of the created (or existing reused) backup file, or
    ``None`` if the source DB is missing.
    """
    from datetime import date, datetime

    if trigger not in ("auto", "manual", "pre-restore", "pre-reset"):
        raise ValueError(f"Unknown backup trigger: {trigger!r}")

    db_path = DATA_DIR / "app.db"
    if not db_path.exists():
        return None

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    backup_path: Path | None = None

    if trigger == "auto":
        today_iso = date.today().isoformat()
        existing_today = sorted(BACKUP_DIR.glob(f"app_{today_iso}_*_auto.db"))
        if existing_today:
            backup_path = existing_today[-1]

    if backup_path is None:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        backup_path = BACKUP_DIR / f"app_{timestamp}_{trigger}.db"
        try:
            src = sqlite3.connect(str(db_path))
            dst = sqlite3.connect(str(backup_path))
            src.backup(dst)
            src.close()
            dst.close()
            logger.info(f"Database backed up to {backup_path}")
        except Exception as e:
            logger.error(f"Database backup failed: {e}", exc_info=True)
            return None

    # Cleanup applies only to auto-backups. Legacy files without a trigger
    # suffix (`app_YYYY-MM-DD.db`) are treated as auto for cleanup purposes.
    auto_backups = sorted(p for p in BACKUP_DIR.glob("app_*.db") if not _is_protected_backup(p))
    for old in auto_backups[:-7]:
        try:
            old.unlink()
            logger.info(f"Removed old backup: {old.name}")
        except OSError as e:
            logger.warning(f"Could not remove old backup {old.name}: {e}")

    return backup_path


def _validate_backup_file(path: Path) -> None:
    """Validate that ``path`` is a SQLite DB with a known Alembic revision.

    Raises ``ValueError`` if any check fails. On success, returns ``None``.
    """
    if not path.exists() or path.stat().st_size < 100:
        raise ValueError("Datei ist leer oder unvollständig.")

    with path.open("rb") as fh:
        header = fh.read(16)
    if not header.startswith(b"SQLite format 3\x00"):
        raise ValueError("Datei ist keine gültige SQLite-Datenbank.")

    try:
        conn = sqlite3.connect(str(path))
        try:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version'")
            if cursor.fetchone() is None:
                raise ValueError("Backup enthält keine Alembic-Versionstabelle und stammt nicht aus dieser App.")
            cursor = conn.execute("SELECT version_num FROM alembic_version")
            row = cursor.fetchone()
            if row is None or not row[0]:
                raise ValueError("Backup enthält keine Alembic-Revision.")
            backup_revision = row[0]
        finally:
            conn.close()
    except sqlite3.DatabaseError as e:
        raise ValueError(f"Backup-Datei nicht lesbar: {e}") from e

    known_revisions = _alembic_known_revisions()
    if known_revisions and backup_revision not in known_revisions:
        raise ValueError(
            f"Backup-Revision '{backup_revision}' ist neuer als die "
            "App-Version. Bitte App aktualisieren, dann erneut versuchen."
        )


def _alembic_known_revisions() -> set[str]:
    """Return the set of revisions known to the bundled Alembic scripts.

    Used to reject backups created with a newer schema than the running app.
    Returns an empty set if Alembic is unavailable (in which case the caller
    skips this check).
    """
    try:
        from alembic.script import ScriptDirectory
    except ImportError:
        return set()

    alembic_cfg = _build_alembic_config()
    if alembic_cfg is None:
        return set()

    try:
        script_dir = ScriptDirectory.from_config(alembic_cfg)
        return {rev.revision for rev in script_dir.walk_revisions()}
    except Exception:
        logger.warning("Failed to enumerate Alembic revisions", exc_info=True)
        return set()


def restore_database(uploaded_db: Path) -> None:
    """Replace the live database with ``uploaded_db`` and migrate to ``head``.

    Caller is responsible for having validated ``uploaded_db`` first via
    :func:`_validate_backup_file`. A ``pre-restore`` safety backup of the
    current DB is created before the swap.
    """
    backup_database(trigger="pre-restore")

    target = DATA_DIR / "app.db"
    engine.dispose()

    for wal_suffix in ("-wal", "-shm"):
        side_file = target.with_name(target.name + wal_suffix)
        try:
            side_file.unlink(missing_ok=True)
        except OSError as e:
            logger.warning(f"Could not remove {side_file.name}: {e}")

    os.replace(uploaded_db, target)
    run_migrations()
    logger.info("Database restored from uploaded backup")


def reset_database() -> None:
    """Delete the live database and re-run migrations to recreate the schema.

    A ``pre-reset`` safety backup of the current DB is created beforehand.
    """
    backup_database(trigger="pre-reset")

    target = DATA_DIR / "app.db"
    engine.dispose()

    for suffix in ("", "-wal", "-shm"):
        side_file = target.with_name(target.name + suffix)
        try:
            side_file.unlink(missing_ok=True)
        except OSError as e:
            logger.warning(f"Could not remove {side_file.name}: {e}")

    run_migrations()
    logger.info("Database reset complete")
