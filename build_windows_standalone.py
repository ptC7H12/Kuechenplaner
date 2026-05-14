#!/usr/bin/env python3
"""
Build-Skript für Windows Standalone Version von Kuechenplaner

Erstellt vollständig eigenständige ZIP-Archive mit embedded Python für Windows.
KEINE Python-Installation erforderlich!

Für macOS/Linux: Verwende die Portable-Version oder Python direkt
"""

import os
import sys
import shutil
import zipfile
import urllib.request
import ssl
import subprocess
from pathlib import Path
from datetime import datetime

from build_logging import setup_build_log

# Projektverzeichnis
PROJECT_ROOT = Path(__file__).parent
BUILD_DIR = PROJECT_ROOT / "build"
RELEASE_DIR = PROJECT_ROOT / "releases"
DOWNLOAD_CACHE = PROJECT_ROOT / ".download_cache"

# Build-Log aktivieren (spiegelt print()-Output nach logs/)
BUILD_LOG_PATH = setup_build_log("standalone", PROJECT_ROOT / "logs")

# Version aus version.txt lesen
VERSION_FILE = PROJECT_ROOT / "version.txt"
try:
    VERSION = VERSION_FILE.read_text().strip()
except Exception:
    VERSION = "1.0.0"  # Fallback

# Python Version für Windows
PYTHON_VERSION = "3.11.9"
PYTHON_URL = f"https://www.python.org/ftp/python/{PYTHON_VERSION}/python-{PYTHON_VERSION}-embed-amd64.zip"
PIP_URL = "https://bootstrap.pypa.io/get-pip.py"

# Dateien die inkludiert werden sollen
INCLUDE_ITEMS = [
    "app/",
    "alembic/",
    "requirements.txt",
    "version.txt",
    "alembic.ini",
    "README.md",
]


def download_file(url: str, destination: Path, description: str = "Datei"):
    """Lädt eine Datei mit Fortschrittsanzeige herunter"""
    print(f"📥 Lade {description} herunter...")
    print(f"   URL: {url}")

    destination.parent.mkdir(parents=True, exist_ok=True)

    ssl_context = ssl.create_default_context()
    headers = {'User-Agent': 'Mozilla/5.0'}
    request = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(request, context=ssl_context) as response:
            total_size = int(response.headers.get('content-length', 0))
            block_size = 8192
            downloaded = 0

            with open(destination, 'wb') as f:
                while True:
                    buffer = response.read(block_size)
                    if not buffer:
                        break

                    downloaded += len(buffer)
                    f.write(buffer)

                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        mb_downloaded = downloaded / (1024 * 1024)
                        mb_total = total_size / (1024 * 1024)
                        print(f"\r   Progress: {percent:.1f}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)", end='')

        print()
        print(f"✅ Download abgeschlossen: {destination.name}")
        return True

    except Exception as e:
        print(f"\n❌ Fehler beim Download: {e}")
        return False


def extract_zip(zip_path: Path, destination: Path):
    """Entpackt ein ZIP-Archiv"""
    print(f"📦 Entpacke {zip_path.name}...")
    destination.mkdir(parents=True, exist_ok=True)

    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(destination)
        print(f"✅ Entpackt nach: {destination}")
        return True
    except Exception as e:
        print(f"❌ Fehler beim Entpacken: {e}")
        return False


def setup_embedded_python(platform_dir: Path) -> bool:
    """Richtet embedded Python für Windows ein"""
    print("\n🐍 Richte embedded Python für Windows ein...")

    python_dir = platform_dir / "python"

    # Download Python embeddable
    cache_file = DOWNLOAD_CACHE / f"python-{PYTHON_VERSION}-embed-amd64.zip"

    if not cache_file.exists():
        if not download_file(PYTHON_URL, cache_file, f"Python {PYTHON_VERSION} Embeddable"):
            return False
    else:
        print(f"✅ Verwende gecachte Datei: {cache_file.name}")

    # Entpacke Python
    if not extract_zip(cache_file, python_dir):
        return False

    # Download get-pip.py
    pip_installer = python_dir / "get-pip.py"
    if not download_file(PIP_URL, pip_installer, "pip installer"):
        return False

    # Aktiviere site-packages und füge Parent-Directory hinzu
    pth_files = list(python_dir.glob("python*._pth"))
    if pth_files:
        pth_file = pth_files[0]
        content = pth_file.read_text()
        content = content.replace("#import site", "import site")

        # Füge notwendige Pfade hinzu
        if "Lib\\site-packages" not in content:
            content += "\nLib\\site-packages\n"

        # Füge Parent-Directory hinzu (wo app/ liegt)
        if ".." not in content:
            content += "..\n"

        pth_file.write_text(content)
        print(f"✅ Site-packages und app-Pfad aktiviert in {pth_file.name}")

    print("✅ Embedded Python eingerichtet")
    return True


def install_dependencies(platform_dir: Path) -> bool:
    """Installiert Python-Dependencies"""
    print(f"\n📦 Installiere Dependencies...")

    python_dir = platform_dir / "python"
    python_exe = python_dir / "python.exe"
    requirements = PROJECT_ROOT / "requirements.txt"

    # Konvertiere zu absoluten Pfaden
    python_exe = python_exe.absolute()
    requirements = requirements.absolute()
    get_pip = (python_dir / "get-pip.py").absolute()

    # Prüfe ob Dateien existieren
    if not python_exe.exists():
        print(f"❌ Python nicht gefunden: {python_exe}")
        return False

    if not get_pip.exists():
        print(f"❌ get-pip.py nicht gefunden: {get_pip}")
        return False

    if not requirements.exists():
        print(f"❌ requirements.txt nicht gefunden: {requirements}")
        return False

    # Installiere pip
    print("  Installing pip...")
    try:
        result = subprocess.run(
            [str(python_exe), str(get_pip), "--no-warn-script-location"],
            cwd=str(python_dir),
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"❌ Pip-Installation fehlgeschlagen")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return False

        print("  ✓ Pip installiert")
    except Exception as e:
        print(f"❌ Fehler bei pip-Installation: {e}")
        return False

    # Installiere Dependencies
    print(f"  Installing requirements...")
    try:
        result = subprocess.run(
            [str(python_exe), "-m", "pip", "install", "-r", str(requirements), "--no-warn-script-location"],
            cwd=str(platform_dir),
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"❌ Dependency-Installation fehlgeschlagen")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return False

        print("  ✓ Dependencies installiert")
    except Exception as e:
        print(f"❌ Fehler bei Dependency-Installation: {e}")
        return False

    print("✅ Dependencies installiert")
    return True


def copy_project_files(target_dir: Path):
    """Kopiert Projektdateien"""
    print(f"📋 Kopiere Projektdateien...")

    for item in INCLUDE_ITEMS:
        source = PROJECT_ROOT / item
        if not source.exists():
            print(f"⚠️  Warnung: {item} nicht gefunden")
            continue

        dest = target_dir / item

        if source.is_dir():
            shutil.copytree(source, dest, dirs_exist_ok=True)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)
        print(f"  ✓ {item}")


def create_startup_script(platform_dir: Path):
    """Erstellt Startup-Skript"""
    script_content = '''@echo off
REM ============================================
REM  Kuechenplaner - Standalone Version
REM  KEINE Python-Installation erforderlich!
REM ============================================

echo.
echo ========================================
echo   Kuechenplaner
echo   Freizeit Rezepturverwaltung
echo ========================================
echo.

REM Wechsle ins Skript-Verzeichnis
cd /d "%~dp0"

REM Verwende embedded Python
set PYTHON_EXE=%~dp0python\\python.exe

if not exist "%PYTHON_EXE%" (
    echo [FEHLER] Embedded Python nicht gefunden!
    echo Bitte stelle sicher, dass der Ordner vollstaendig entpackt wurde.
    pause
    exit /b 1
)

echo [INFO] Verwende embedded Python

REM Erstelle Datenbank-Verzeichnis
if not exist "data" mkdir data

REM Start the application
echo.
echo ========================================
echo   Starte Anwendung
echo ========================================
echo.
echo Druecke Ctrl+C um die Anwendung zu beenden
echo.

REM Starte Server (mit WebView)
"%PYTHON_EXE%" -m app.main

if errorlevel 1 (
    echo.
    echo [FEHLER] Anwendung wurde mit Fehler beendet!
    pause
)
'''

    script_path = platform_dir / "start.bat"
    script_path.write_text(script_content, encoding='utf-8')
    print(f"✅ Startup-Skript erstellt: start.bat")


def create_readme(platform_dir: Path):
    """Erstellt README"""
    readme_content = f"""# Kuechenplaner - Windows Standalone Version

## ✨ Keine Installation erforderlich!

Diese Version enthält alles, was Sie brauchen - einschließlich Python!

## Schnellstart

1. **Doppelklick auf `start.bat`**
2. Fertig! Die Anwendung startet automatisch

## Das wars!

Keine Python-Installation, keine Konfiguration, keine Kommandozeile erforderlich.
Einfach entpacken und starten!

## Technische Details

- Enthält: Python {PYTHON_VERSION} (embedded)
- Größe: ~60 MB (komprimiert)
- Portable: Kann auf USB-Stick verwendet werden
- Datenbank: Wird lokal im data-Ordner gespeichert

## Bei Problemen

### Windows Defender Firewall Warnung
- Klicken Sie auf "Zugriff zulassen" - dies ist normal für lokale Server

### Port bereits belegt
- Schließen Sie andere Programme die den Port nutzen
- Oder ändern Sie den Port in den Einstellungen

## Support

Bei Fragen oder Problemen: GitHub Issues

## Hinweis für macOS/Linux Benutzer

Für macOS und Linux verwenden Sie bitte Python direkt:
```bash
pip install -r requirements.txt
python -m app.main
```
"""

    readme_path = platform_dir / "README.txt"
    readme_path.write_text(readme_content, encoding='utf-8')
    print(f"✅ README erstellt")


def clean_standalone_windows_files():
    """Entfernt nur Dateien, die von diesem Skript erstellt wurden"""
    print("🧹 Räume alte Windows-Standalone-Builds auf...")

    # Lösche spezifischen Build-Ordner
    standalone_build_dir = BUILD_DIR / "Kuechenplaner-Windows-Standalone"
    if standalone_build_dir.exists():
        shutil.rmtree(standalone_build_dir)
        print(f"  ✓ Entfernt: {standalone_build_dir.name}")

    # Lösche nur Windows-Standalone Release-Dateien
    if RELEASE_DIR.exists():
        for release_file in RELEASE_DIR.glob("Kuechenplaner-*-windows-standalone-*.zip"):
            release_file.unlink()
            print(f"  ✓ Entfernt: {release_file.name}")

    # Erstelle Verzeichnisse falls nicht vorhanden
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)
    DOWNLOAD_CACHE.mkdir(parents=True, exist_ok=True)

    print("✅ Aufgeräumt!\n")


def create_package():
    """Erstellt Windows Standalone-Paket"""
    print("\n" + "="*60)
    print("🚀 Kuechenplaner - Windows Standalone Build")
    print(f"📌 Version: {VERSION}")
    print(f"📝 Log:     {BUILD_LOG_PATH}")
    print("="*60 + "\n")

    # Vorbereitung - Lösche nur eigene Dateien
    clean_standalone_windows_files()

    # Erstelle Build-Verzeichnis
    platform_dir = BUILD_DIR / "Kuechenplaner-Windows-Standalone"
    platform_dir.mkdir(parents=True, exist_ok=True)

    # Build-Schritte
    try:
        copy_project_files(platform_dir)

        if not setup_embedded_python(platform_dir):
            raise Exception("Python Setup fehlgeschlagen")

        if not install_dependencies(platform_dir):
            raise Exception("Dependency Installation fehlgeschlagen")

        create_startup_script(platform_dir)
        create_readme(platform_dir)

        # Erstelle ZIP
        timestamp = datetime.now().strftime("%Y%m%d")
        zip_name = f"Kuechenplaner-{VERSION}-windows-standalone-{timestamp}.zip"
        zip_path = RELEASE_DIR / zip_name

        print(f"\n🗜️  Erstelle ZIP-Archiv: {zip_name}")
        print("   Dies kann einige Minuten dauern...")

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(platform_dir):
                dirs[:] = [d for d in dirs if d not in ['__pycache__', '.pytest_cache']]

                for file in files:
                    if file.endswith('.pyc'):
                        continue

                    file_path = Path(root) / file
                    arcname = file_path.relative_to(BUILD_DIR)
                    zipf.write(file_path, arcname)

        size_mb = zip_path.stat().st_size / (1024 * 1024)

        print(f"\n✅ {zip_name} erstellt ({size_mb:.1f} MB)")

        print("\n" + "="*60)
        print("✨ Build erfolgreich abgeschlossen!")
        print("="*60)
        print(f"\n📁 Release: {zip_path.absolute()}\n")
        print("💡 Nächste Schritte:")
        print("  1. Teste das ZIP-Archiv auf einem Windows-PC")
        print("  2. Lade es auf GitHub Releases hoch")
        print("  3. Teile den Download-Link mit Benutzern")
        print()

    except Exception as e:
        print(f"\n❌ Build fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    try:
        create_package()
    except KeyboardInterrupt:
        print("\n\n⚠️  Build abgebrochen")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Kritischer Fehler: {e}")
        sys.exit(1)
