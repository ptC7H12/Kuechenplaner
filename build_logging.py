"""Build-Logging-Helper.

Spiegelt `print()`-Ausgaben der Build-Skripte (`build.py`,
`build_windows_standalone.py`, `excel_import.py`) zusaetzlich nach
`logs/build_<script>_<timestamp>.log`. Auf der Konsole bleibt alles
unveraendert, damit Build-Aufrufe weiter interaktiv bleiben.

Verwendung in einem Build-Skript (ganz oben, vor allen Imports, die Output
erzeugen):

    from build_logging import setup_build_log
    LOG_PATH = setup_build_log("build")  # liefert Pfad zur Logdatei

Bei Fehlern kann man dem Nutzer dann sagen: "Details siehe {LOG_PATH}".
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path


class _Tee:
    """Schreibt parallel auf zwei Streams (typisch: stdout + Datei)."""

    def __init__(self, *streams):
        self._streams = streams

    def write(self, data):
        for stream in self._streams:
            try:
                stream.write(data)
            except Exception:
                # Defensive: ein toter Stream darf den Build nicht killen.
                pass

    def flush(self):
        for stream in self._streams:
            try:
                stream.flush()
            except Exception:
                pass

    def isatty(self):
        # An den ersten Stream durchreichen (typisch: das echte stdout).
        first = self._streams[0]
        return getattr(first, "isatty", lambda: False)()


def setup_build_log(script_name: str, log_dir: Path | None = None) -> Path:
    """Aktiviert stdout/stderr-Tee in eine Build-Logdatei.

    Args:
        script_name: Praefix fuer die Logdatei, z.B. "build" oder "standalone".
        log_dir: Optionales Verzeichnis. Default: `<repo_root>/logs/`.

    Returns:
        Pfad zur erzeugten Logdatei.
    """
    if log_dir is None:
        log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = log_dir / f"build_{script_name}_{timestamp}.log"

    log_file = open(log_path, "w", encoding="utf-8", buffering=1)

    # Header in die Datei schreiben — beim Debuggen sehr hilfreich.
    log_file.write(f"=== Build-Log: {script_name} ===\n")
    log_file.write(f"Started: {datetime.now().isoformat()}\n")
    log_file.write(f"Python:  {sys.version}\n")
    log_file.write(f"Platform: {sys.platform}\n")
    log_file.write("=" * 60 + "\n\n")
    log_file.flush()

    # stdout/stderr wraps mit Tee
    if sys.stdout is not None:
        sys.stdout = _Tee(sys.stdout, log_file)
    if sys.stderr is not None:
        sys.stderr = _Tee(sys.stderr, log_file)

    return log_path
