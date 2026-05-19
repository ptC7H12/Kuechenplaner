"""Tests for Story 27: manual backup download endpoint, timestamped filenames,
cleanup that preserves manual backups."""

import re
import sqlite3

import pytest

from app import database as db_module
from app.database import backup_database as _backup_database


@pytest.fixture
def temp_data_dir(tmp_path, monkeypatch):
    """Redirect DATA_DIR/BACKUP_DIR to a temp location and seed a minimal DB."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    backup_dir = data_dir / "backups"

    db_path = data_dir / "app.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE t (id INTEGER)")
    conn.commit()
    conn.close()

    monkeypatch.setattr(db_module, "DATA_DIR", data_dir)
    monkeypatch.setattr(db_module, "BACKUP_DIR", backup_dir)
    return data_dir, backup_dir


FILENAME_PATTERN = re.compile(
    r"^app_(\d{4}-\d{2}-\d{2})_(\d{6})_(auto|manual)\.db$"
)


def test_manual_backup_filename_is_parseable(temp_data_dir):
    _, backup_dir = temp_data_dir
    path = _backup_database(trigger="manual")

    assert path is not None
    assert path.exists()
    assert path.parent == backup_dir

    match = FILENAME_PATTERN.match(path.name)
    assert match is not None, f"Unparseable filename: {path.name}"
    assert match.group(3) == "manual"


def test_auto_backup_only_one_per_day(temp_data_dir):
    _, backup_dir = temp_data_dir
    first = _backup_database(trigger="auto")
    second = _backup_database(trigger="auto")

    assert first is not None and second is not None
    assert first == second
    autos = sorted(backup_dir.glob("app_*_auto.db"))
    assert len(autos) == 1


def test_cleanup_keeps_last_7_auto_and_all_manual(temp_data_dir):
    _, backup_dir = temp_data_dir
    backup_dir.mkdir(parents=True, exist_ok=True)

    for day in range(1, 11):
        (backup_dir / f"app_2026-01-{day:02d}_120000_auto.db").write_bytes(b"x")
    for day in range(1, 4):
        (backup_dir / f"app_2026-01-{day:02d}_120000_manual.db").write_bytes(b"x")

    _backup_database(trigger="manual")

    autos = sorted(backup_dir.glob("app_*_auto.db"))
    manuals = sorted(backup_dir.glob("app_*_manual.db"))
    assert len(autos) == 7
    assert len(manuals) == 4  # 3 pre-existing + 1 new

    surviving_days = {int(p.name.split("-")[2][:2]) for p in autos}
    assert surviving_days == {4, 5, 6, 7, 8, 9, 10}


def test_cleanup_tolerates_legacy_auto_filenames(temp_data_dir):
    """Old-format `app_YYYY-MM-DD.db` files (no trigger suffix) are treated as
    auto-backups for cleanup — they must not crash the cleanup glob."""
    _, backup_dir = temp_data_dir
    backup_dir.mkdir(parents=True, exist_ok=True)

    for day in range(1, 11):
        (backup_dir / f"app_2026-01-{day:02d}.db").write_bytes(b"x")

    _backup_database(trigger="manual")

    legacy = [p for p in backup_dir.glob("app_*.db") if not p.stem.endswith("_manual")]
    manuals = [p for p in backup_dir.glob("app_*.db") if p.stem.endswith("_manual")]
    assert len(legacy) == 7
    assert len(manuals) == 1


def test_download_endpoint_returns_file_with_manual_filename(client, temp_data_dir):
    response = client.get("/settings/database/download")

    assert response.status_code == 200
    cd = response.headers.get("content-disposition", "")
    match = re.search(r'filename="?(app_[^";]+\.db)"?', cd)
    assert match is not None, f"No filename in Content-Disposition: {cd}"
    filename = match.group(1)

    parsed = FILENAME_PATTERN.match(filename)
    assert parsed is not None, f"Unparseable filename from endpoint: {filename}"
    assert parsed.group(3) == "manual"
