"""Tests for ``_read_version`` fallback resolution in app.routers.settings."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from app.routers import settings as settings_module


@pytest.fixture
def isolated_version_lookup(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """Force every candidate path to point inside ``tmp_path``.

    Layout::

        tmp_path/
            repo/version.txt         (parents[2] fallback)
            install/_internal/KuechenApp.exe  (sys.executable fallback)
            install/version.txt      (exe_dir.parent fallback)
    """
    monkeypatch.delenv("APP_VERSION", raising=False)

    repo_root = tmp_path / "repo"
    pkg_routers = repo_root / "app" / "routers"
    pkg_routers.mkdir(parents=True)
    fake_module_file = pkg_routers / "settings.py"
    fake_module_file.write_text("# placeholder", encoding="utf-8")

    install_dir = tmp_path / "install"
    internal_dir = install_dir / "_internal"
    internal_dir.mkdir(parents=True)
    fake_exe = internal_dir / "KuechenApp.exe"
    fake_exe.write_text("", encoding="utf-8")

    monkeypatch.setattr(settings_module, "__file__", str(fake_module_file))
    monkeypatch.setattr(sys, "executable", str(fake_exe))

    return {
        "repo_version": repo_root / "version.txt",
        "exe_dir_version": internal_dir / "version.txt",
        "exe_parent_version": install_dir / "version.txt",
    }


def test_env_override_wins(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("APP_VERSION", "9.9.9")
    assert settings_module._read_version() == "9.9.9"


def test_reads_from_repo_root(isolated_version_lookup: dict[str, Path]) -> None:
    isolated_version_lookup["repo_version"].write_text("1.2.3\n", encoding="utf-8")
    assert settings_module._read_version() == "1.2.3"


def test_reads_from_exe_dir_when_repo_missing(isolated_version_lookup: dict[str, Path]) -> None:
    isolated_version_lookup["exe_dir_version"].write_text("4.5.6\n", encoding="utf-8")
    assert settings_module._read_version() == "4.5.6"


def test_reads_from_exe_parent_when_others_missing(isolated_version_lookup: dict[str, Path]) -> None:
    isolated_version_lookup["exe_parent_version"].write_text("7.8.9\n", encoding="utf-8")
    assert settings_module._read_version() == "7.8.9"


def test_repo_root_preferred_over_exe_dir(isolated_version_lookup: dict[str, Path]) -> None:
    isolated_version_lookup["repo_version"].write_text("1.0.0\n", encoding="utf-8")
    isolated_version_lookup["exe_dir_version"].write_text("2.0.0\n", encoding="utf-8")
    assert settings_module._read_version() == "1.0.0"


def test_returns_unknown_when_no_file(isolated_version_lookup: dict[str, Path]) -> None:
    assert settings_module._read_version() == "unknown"
