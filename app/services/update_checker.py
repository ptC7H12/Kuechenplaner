"""GitHub release update check.

Queries the latest published GitHub release and compares it against the running
``APP_VERSION``. All network/parse failures are swallowed: a failed check simply
reports ``update_available=False``. Results are cached module-wide so GitHub is
queried at most once per ``UPDATE_CHECK_INTERVAL`` regardless of how often the
frontend polls.
"""

import json
import time
import urllib.request

from app.constants import GITHUB_API_LATEST_RELEASE, REPO_URL
from app.logging_config import get_logger

logger = get_logger("update_checker")

# Re-query GitHub at most every 2 hours.
UPDATE_CHECK_INTERVAL = 2 * 60 * 60

_cache: dict = {"timestamp": 0.0, "result": None}


def _parse_version(value: str) -> tuple[int, ...] | None:
    """Parse a dotted version string into a comparable int tuple.

    Returns ``None`` when the value is empty or contains a non-numeric segment.
    """
    if not value:
        return None
    parts = []
    for segment in value.split("."):
        if not segment.isdigit():
            return None
        parts.append(int(segment))
    return tuple(parts) if parts else None


def _fetch_latest_release() -> dict:
    """Fetch the latest release JSON from the GitHub API (raises on failure)."""
    request = urllib.request.Request(
        GITHUB_API_LATEST_RELEASE,
        headers={"User-Agent": "Kuechenplaner-UpdateChecker", "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(request, timeout=5) as response:  # noqa: S310 — fixed HTTPS GitHub API URL
        return json.loads(response.read().decode("utf-8"))


def check_for_update(force: bool = False, current_version: str | None = None) -> dict:
    """Return cached update info, refreshing from GitHub when the cache is stale.

    Result shape::

        {"update_available": bool, "current_version": str,
         "latest_version": str | None, "release_url": str}
    """
    global _cache

    if current_version is None:
        from app.routers.settings import APP_VERSION

        current_version = APP_VERSION

    now = time.monotonic()
    cached = _cache["result"]
    if not force and cached is not None and (now - _cache["timestamp"]) < UPDATE_CHECK_INTERVAL:
        return cached

    result = {
        "update_available": False,
        "current_version": current_version,
        "latest_version": None,
        "release_url": f"{REPO_URL}/releases",
    }

    if current_version and current_version != "unknown":
        try:
            data = _fetch_latest_release()
            latest = str(data.get("tag_name", "")).lstrip("v").strip()
            current_tuple = _parse_version(current_version)
            latest_tuple = _parse_version(latest)
            if latest_tuple is not None and current_tuple is not None and latest_tuple > current_tuple:
                result["update_available"] = True
                result["latest_version"] = latest
                result["release_url"] = data.get("html_url") or f"{REPO_URL}/releases"
            elif latest:
                result["latest_version"] = latest
        except Exception:
            logger.debug("Update check failed", exc_info=True)

    _cache = {"timestamp": now, "result": result}
    return result
