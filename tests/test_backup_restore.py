"""Tests for Story 28: backup restore endpoint + file validation."""

from __future__ import annotations

import io
import sqlite3
from pathlib import Path

import pytest

from app import database as db_module
from app.database import _validate_backup_file
from app.routers import settings as settings_router

# Capture the real backup helper before the autouse `_disable_lifespan_side_effects`
# fixture neuters it — we want the real implementation back inside the restore_env.
_REAL_BACKUP_DATABASE = db_module.backup_database

HEAD_REVISION = "006"  # latest revision in alembic/versions/


def _write_backup_db(path: Path, revision: str = HEAD_REVISION) -> None:
    """Create a minimal but valid SQLite backup with an alembic_version row."""
    conn = sqlite3.connect(str(path))
    try:
        conn.execute("CREATE TABLE alembic_version (version_num VARCHAR(32) PRIMARY KEY)")
        conn.execute("INSERT INTO alembic_version VALUES (?)", (revision,))
        conn.execute("CREATE TABLE camps (id INTEGER PRIMARY KEY, name TEXT)")
        conn.commit()
    finally:
        conn.close()


def _fake_run_migrations() -> None:
    """Stand-in for Alembic in tests: just stamp the head revision.

    Alembic would target the bundled config (production DB path), which is
    pointless against the redirected test DATA_DIR. The endpoints only care
    that a valid DB with `alembic_version` exists after the call.
    """
    target = db_module.DATA_DIR / "app.db"
    conn = sqlite3.connect(str(target))
    try:
        conn.execute("CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) PRIMARY KEY)")
        conn.execute("DELETE FROM alembic_version")
        conn.execute("INSERT INTO alembic_version VALUES (?)", (HEAD_REVISION,))
        conn.commit()
    finally:
        conn.close()


@pytest.fixture
def restore_env(tmp_path, monkeypatch):
    """Redirect DATA_DIR/BACKUP_DIR and put a real DB at the live path."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    backup_dir = data_dir / "backups"
    backup_dir.mkdir()
    _write_backup_db(data_dir / "app.db")

    monkeypatch.setattr(db_module, "DATA_DIR", data_dir)
    monkeypatch.setattr(db_module, "BACKUP_DIR", backup_dir)
    monkeypatch.setattr(settings_router, "DATA_DIR", data_dir)
    monkeypatch.setattr(db_module, "backup_database", _REAL_BACKUP_DATABASE)
    monkeypatch.setattr(db_module, "run_migrations", _fake_run_migrations)

    return data_dir, backup_dir


def _set_cookies(response) -> list[str]:
    """Return raw Set-Cookie header values from a TestClient response."""
    return response.headers.get_list("set-cookie")


# ---------- _validate_backup_file ----------


def test_validate_accepts_head_revision(tmp_path):
    backup = tmp_path / "good.db"
    _write_backup_db(backup, revision=HEAD_REVISION)
    _validate_backup_file(backup)  # raises nothing


def test_validate_rejects_non_sqlite(tmp_path):
    bogus = tmp_path / "bogus.db"
    bogus.write_bytes(b"definitely not a sqlite database file" * 10)
    with pytest.raises(ValueError, match="SQLite"):
        _validate_backup_file(bogus)


def test_validate_rejects_missing_alembic_table(tmp_path):
    db = tmp_path / "noalembic.db"
    conn = sqlite3.connect(str(db))
    conn.execute("CREATE TABLE foo (id INTEGER)")
    conn.execute("INSERT INTO foo VALUES (1)")
    conn.commit()
    conn.close()
    with pytest.raises(ValueError, match="Alembic"):
        _validate_backup_file(db)


def test_validate_rejects_unknown_revision(tmp_path):
    db = tmp_path / "future.db"
    _write_backup_db(db, revision="999_future_revision")
    with pytest.raises(ValueError, match="neuer als"):
        _validate_backup_file(db)


# ---------- /settings/database/restore ----------


def test_restore_endpoint_happy_path(client, restore_env):
    data_dir, backup_dir = restore_env

    upload_db = data_dir.parent / "upload.db"
    _write_backup_db(upload_db, revision=HEAD_REVISION)
    conn = sqlite3.connect(str(upload_db))
    conn.execute("INSERT INTO camps (id, name) VALUES (4242, 'Restored')")
    conn.commit()
    conn.close()

    client.cookies.set("current_camp_id", "7")
    with upload_db.open("rb") as fh:
        response = client.post(
            "/settings/database/restore",
            files={"backup_file": ("backup.db", fh, "application/octet-stream")},
        )

    assert response.status_code == 200
    assert response.headers.get("hx-refresh") == "true"

    set_cookies = _set_cookies(response)
    assert any(c.startswith("flash_toast=") for c in set_cookies)
    assert any(c.startswith("current_camp_id=") and "Max-Age=0" in c for c in set_cookies)

    pre_restore_backups = list(backup_dir.glob("app_*_pre-restore.db"))
    assert len(pre_restore_backups) == 1

    live_db = data_dir / "app.db"
    conn = sqlite3.connect(str(live_db))
    rows = conn.execute("SELECT id FROM camps ORDER BY id").fetchall()
    conn.close()
    assert (4242,) in rows


def test_restore_endpoint_rejects_non_db_extension(client, restore_env):
    response = client.post(
        "/settings/database/restore",
        files={
            "backup_file": (
                "notes.zip",
                io.BytesIO(b"zip data placeholder"),
                "application/zip",
            )
        },
    )
    assert response.status_code == 400
    assert "hx-trigger" in {h.lower() for h in response.headers}


def test_restore_endpoint_rejects_invalid_content(client, restore_env):
    data_dir, backup_dir = restore_env

    response = client.post(
        "/settings/database/restore",
        files={
            "backup_file": (
                "garbage.db",
                io.BytesIO(b"not really sqlite payload"),
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 400
    assert "hx-trigger" in {h.lower() for h in response.headers}
    # No pre-restore safety backup is created when validation fails.
    assert list(backup_dir.glob("app_*_pre-restore.db")) == []
    # And no leftover temp upload files linger in DATA_DIR.
    assert list(data_dir.glob("app_restore_*.tmp")) == []
