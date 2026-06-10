"""Tests for Story 32: GitHub release update check (service + cache)."""

import pytest

from app.services import update_checker


@pytest.fixture(autouse=True)
def reset_cache():
    """Reset the module-wide cache before each test."""
    update_checker._cache = {"timestamp": 0.0, "result": None}
    yield
    update_checker._cache = {"timestamp": 0.0, "result": None}


def test_update_available(monkeypatch):
    monkeypatch.setattr(
        update_checker,
        "_fetch_latest_release",
        lambda: {"tag_name": "v9.9.9", "html_url": "https://github.com/ptC7H12/Kuechenplaner/releases/tag/v9.9.9"},
    )

    result = update_checker.check_for_update(force=True, current_version="1.5.0")

    assert result["update_available"] is True
    assert result["latest_version"] == "9.9.9"
    assert result["release_url"].endswith("v9.9.9")


def test_no_update_when_same_or_lower(monkeypatch):
    monkeypatch.setattr(update_checker, "_fetch_latest_release", lambda: {"tag_name": "v1.5.0"})

    same = update_checker.check_for_update(force=True, current_version="1.5.0")
    assert same["update_available"] is False
    assert same["latest_version"] == "1.5.0"

    update_checker._cache = {"timestamp": 0.0, "result": None}
    monkeypatch.setattr(update_checker, "_fetch_latest_release", lambda: {"tag_name": "v1.0.0"})
    lower = update_checker.check_for_update(force=True, current_version="1.5.0")
    assert lower["update_available"] is False


def test_network_error_is_swallowed(monkeypatch):
    def boom():
        raise OSError("no network")

    monkeypatch.setattr(update_checker, "_fetch_latest_release", boom)

    result = update_checker.check_for_update(force=True, current_version="1.5.0")

    assert result["update_available"] is False
    assert result["current_version"] == "1.5.0"


def test_unknown_version_skips_remote(monkeypatch):
    calls = {"count": 0}

    def counting_fetch():
        calls["count"] += 1
        return {"tag_name": "v9.9.9"}

    monkeypatch.setattr(update_checker, "_fetch_latest_release", counting_fetch)

    result = update_checker.check_for_update(force=True, current_version="unknown")

    assert result["update_available"] is False
    assert calls["count"] == 0


def test_cache_prevents_second_remote_call(monkeypatch):
    calls = {"count": 0}

    def counting_fetch():
        calls["count"] += 1
        return {"tag_name": "v9.9.9", "html_url": "https://example.test/v9.9.9"}

    monkeypatch.setattr(update_checker, "_fetch_latest_release", counting_fetch)

    first = update_checker.check_for_update(current_version="1.5.0")
    second = update_checker.check_for_update(current_version="1.5.0")

    assert calls["count"] == 1
    assert first == second
    assert first["update_available"] is True
