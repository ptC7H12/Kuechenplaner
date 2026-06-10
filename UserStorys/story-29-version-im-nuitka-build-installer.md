# Story 29: Versionsanzeige im Nuitka-Build/Installer reparieren

**Status:** Review
**Aufwand:** Klein
**Machbarkeit:** Sehr gut
**Implementiert in:** `app/routers/settings.py:38-77`, `build.py:42`, `build.bat:75,138`, `tests/test_settings_version.py`

## Beschreibung

Als Anwender möchte ich auf der Einstellungen-Seite unter "Info" immer die tatsächliche App-Version aus `version.txt` sehen — unabhängig davon, ob die App über `run_build_standalone.bat` (embedded Python) oder über `build.bat standalone` + Inno-Setup-Installer gebaut und installiert wurde. Aktuell steht im Nuitka-/Installer-Build dort "unknown", während der embedded-Python-Build die Version korrekt anzeigt.

## Ist-Zustand

- `app/routers/settings.py:38-45` — `_read_version()` liest `version.txt` über `Path(__file__).resolve().parents[2] / "version.txt"`. Bei `OSError` Fallback `"unknown"`. Im Nuitka-Standalone zeigt `__file__` in den `_internal/`-Bundle-Ordner; `parents[2]` zeigt damit nicht auf einen Ort, an dem `version.txt` liegt.
- `build.py:36-103` (`build()`) und `build.bat:59-128` (`debug`-/`standalone`-Mode) — listen alle `--include-data-file`/`--include-data-dir`-Argumente von Nuitka auf, **ohne** `version.txt` mit ins Bundle aufzunehmen. Die Datei ist im kompilierten Output nicht vorhanden.
- `installer.iss:68-73` — Inno-`[Files]`-Sektion kopiert nur `dist\_internal\*`. `version.txt` wird, selbst wenn sie neben der Build-Ausgabe läge, **nicht** ins Installationsverzeichnis kopiert.
- `build_windows_standalone.py:45-52, 233-246` — `INCLUDE_ITEMS` enthält explizit `"version.txt"` und kopiert sie ins Standalone-Paket-Root. Deshalb funktioniert dieser Pfad: `parents[2]` (von `app/routers/settings.py`) zeigt im Standalone-Layout auf das Paket-Root, in dem `version.txt` liegt.
- `installer.iss:13-15` und `build.bat:117` / `build.py:180-182` — die Version wird zur Build-Zeit korrekt aus `version.txt` ausgelesen und an Inno-Setup übergeben (`AppVersion`), aber zur Laufzeit existiert in `_internal/` keine `version.txt` mehr für die App.

## Akzeptanzkriterien

- [x] Nach `build.bat standalone` zeigt die installierte App (Installer-Setup) unter Einstellungen → Info die Version aus `version.txt` an (nicht "unknown").
- [x] Nach `build.bat debug` zeigt der Debug-Build dieselbe korrekte Version an.
- [x] Nach `run_build_standalone.bat` zeigt der embedded-Python-Build weiterhin die korrekte Version (Regression vermeiden).
- [x] Dev-Modus (`DEVELOPMENT=1 python -m app.main`) zeigt die Version aus dem Repo-Root korrekt an.
- [x] `_read_version()` greift auf einen robusten Suchpfad zurück (z. B. neben `sys.executable`, neben dem Paket-Root, neben `_internal/`) statt fest `parents[2]`.
- [x] Pytest deckt ab: `_read_version()` findet `version.txt` über die definierten Fallback-Pfade und liefert `"unknown"` nur, wenn an keiner der Stellen eine Datei existiert.

## Technische Umsetzung (Vorschlag)

### Build

- `build.py:36-103` und `build.bat:65-106` (`debug`-Mode) sowie `build.bat:131-141` (`fast`-Mode): Argument `--include-data-file=version.txt=version.txt` ergänzen, damit Nuitka `version.txt` neben die Bundle-Module legt.
- `installer.iss:68-73`: zusätzliche `Source: "version.txt"; DestDir: "{app}\_internal"; Flags: ignoreversion`-Zeile aufnehmen (oder den Pfad wählen, in den Nuitka die Datei legt), damit die Datei vom Installer mitkopiert wird.

### Backend

- `app/routers/settings.py:38-45`: `_read_version()` so umbauen, dass mehrere Kandidatenpfade probiert werden, jeweils per `Path.read_text()` mit `try/except OSError`:
  1. `Path(__file__).resolve().parents[2] / "version.txt"` (Dev-/Standalone-Repo-Layout)
  2. `Path(sys.executable).resolve().parent / "version.txt"` (Nuitka `_internal/`)
  3. `Path(sys.executable).resolve().parent.parent / "version.txt"` (falls Datei eine Ebene über `_internal/` landet)
  4. Optionaler ENV-Override (`APP_VERSION`) zuerst lesen — erleichtert Tests.
  - Erst wenn alle Kandidaten fehlschlagen, `"unknown"` zurückgeben.
- Modul-Konstante `APP_VERSION` bleibt; nichts an der Template-Seite ändern.

### Tests

- Neuer Test in `tests/test_settings_router.py` (oder vorhandenes Settings-Test-Modul): legt `version.txt` über `monkeypatch`/`tmp_path` an einem der Fallback-Pfade an und prüft, dass `_read_version()` den Inhalt zurückgibt; weiterer Fall: keine Datei vorhanden → `"unknown"`.
