"""
Simplified logging configuration for Kuechenplaner
Single log file with rotation
"""
import logging
import os
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler


def _get_log_dir() -> Path:
    """Return a writable directory for log files."""
    if "__compiled__" in globals():
        if sys.platform == "win32":
            base = Path(os.environ.get("APPDATA", str(Path.home()))) / "KuechenApp" / "logs"
        else:
            xdg = os.environ.get("XDG_DATA_HOME", "")
            base = (Path(xdg) if xdg else Path.home() / ".local" / "share") / "KuechenApp" / "logs"
    else:
        base = Path("logs")
    base.mkdir(parents=True, exist_ok=True)
    return base


def setup_logging(log_level: str = "INFO"):
    """
    Configure application-wide logging with single log file

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """

    level = getattr(logging, log_level.upper(), logging.INFO)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler (always safe)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler — wrapped in try/except so a PermissionError
    # never prevents the application from starting.
    try:
        log_dir = _get_log_dir()
        file_handler = RotatingFileHandler(
            log_dir / "kuechenplaner.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except OSError as exc:
        root_logger.warning("File logging disabled: %s", exc)

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("watchfiles").setLevel(logging.WARNING)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module

    Args:
        name: Module name (e.g., 'crud', 'recipes', 'calculation')

    Returns:
        Logger instance
    """
    return logging.getLogger(f"kuechenplaner.{name}")
