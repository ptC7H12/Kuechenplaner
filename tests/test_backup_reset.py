"""Tests for Story 28: database reset endpoint."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from app import database as db_module
from app.routers import settings as settings_router

_REAL_BACKUP_DATABASE = db_module.backup_database

HEAD_REVISION = "006"


def _write_live_db(path: Path) -> None:
    conn = sqlite3.connect(str(path))
    try:
        conn.execute("CREATE TABLE alembic_version (version_num VARCHAR(32) PRIMARY KEY)")
        conn.execute("INSERT INTO alembic_version VALUES (?)", (HEAD_REVISION,))
        conn.execute("CREATE TABLE camps (id INTEGER PRIMARY KEY, name TEXT)")
        conn.execute("INSERT INTO camps (id, name) VALUES (1, 'Soon Wiped')")
        conn.commit()
    finally:
        conn.close()


def _fake_run_migrations() -> None:
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
def reset_env(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    backup_dir = data_dir / "backups"
    backup_dir.mkdir()
    _write_live_db(data_dir / "app.db")

    monkeypatch.setattr(db_module, "DATA_DIR", data_dir)
    monkeypatch.setattr(db_module, "BACKUP_DIR", backup_dir)
    monkeypatch.setattr(settings_router, "DATA_DIR", data_dir)
    monkeypatch.setattr(db_module, "backup_database", _REAL_BACKUP_DATABASE)
    monkeypatch.setattr(db_module, "run_migrations", _fake_run_migrations)

    return data_dir, backup_dir


def test_reset_endpoint_happy_path(client, reset_env):
    data_dir, backup_dir = reset_env

    client.cookies.set("current_camp_id", "7")
    response = client.post("/settings/database/reset")

    assert response.status_code == 200
    assert response.headers.get("hx-refresh") == "true"

    set_cookies = response.headers.get_list("set-cookie")
    assert any(c.startswith("flash_toast=") for c in set_cookies)
    assert any(c.startswith("current_camp_id=") and "Max-Age=0" in c for c in set_cookies)

    pre_reset_backups = list(backup_dir.glob("app_*_pre-reset.db"))
    assert len(pre_reset_backups) == 1

    live_db = data_dir / "app.db"
    assert live_db.exists(), "reset must leave a fresh DB at the live path"

    conn = sqlite3.connect(str(live_db))
    try:
        version_row = conn.execute("SELECT version_num FROM alembic_version").fetchone()
        # The pre-wipe `camps` table is gone — only the bare migration schema remains.
        camps_table = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='camps'").fetchone()
    finally:
        conn.close()

    assert version_row == (HEAD_REVISION,)
    assert camps_table is None
