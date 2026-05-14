"""Shared pytest fixtures.

The fixtures here build a fully isolated FastAPI app instance backed by an
in-memory SQLite DB so tests stay deterministic and never touch the user's
real `data/app.db`. The lifespan (which runs Alembic migrations + seeders) is
deliberately bypassed — we use `Base.metadata.create_all` against the test
engine instead.
"""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Prevent app/main.py from importing pywebview at module-import time.
os.environ.setdefault("DEVELOPMENT", "1")

from app import main as app_main  # noqa: E402
from app.database import Base, get_db  # noqa: E402


@pytest.fixture(scope="function")
def test_engine():
    """Fresh in-memory SQLite for each test (full isolation)."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_engine):
    """Per-test SQLAlchemy session."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(test_engine):
    """TestClient with the DB dependency overridden to the in-memory engine.

    The app's lifespan is not executed (TestClient by default does run it,
    but our lifespan calls `backup_database()` and `run_migrations()` on the
    real production DB path — so we override `get_db` *before* requests fire).
    """
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app_main.app.dependency_overrides[get_db] = override_get_db
    # Disable lifespan so backup_database / run_migrations / seeders are skipped.
    with TestClient(app_main.app, raise_server_exceptions=True) as c:
        # Note: TestClient's context manager triggers lifespan. We swallow any
        # error by replacing run_migrations with a no-op at import time below.
        yield c
    app_main.app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def _disable_lifespan_side_effects(monkeypatch):
    """Lifespan calls backup_database/run_migrations/init_default_data.
    For tests these touch the real DB path, so replace them with no-ops."""
    from app import database as db_module
    from app import seeders as seeders_module

    monkeypatch.setattr(db_module, "backup_database", lambda: None)
    monkeypatch.setattr(db_module, "run_migrations", lambda: None)
    monkeypatch.setattr(seeders_module, "init_default_data", lambda: None)
    # main.py imported these names directly, so also patch the bound refs.
    monkeypatch.setattr(app_main, "backup_database", lambda: None, raising=False)
    monkeypatch.setattr(app_main, "run_migrations", lambda: None, raising=False)
    monkeypatch.setattr(app_main, "init_default_data", lambda: None, raising=False)
