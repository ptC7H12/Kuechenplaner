#!/usr/bin/env python3
"""
Nuitka Build Script für Freizeit Rezepturverwaltung
Kompiliert die Anwendung zu einer standalone Desktop-App
"""

import subprocess
import sys
import os
from pathlib import Path

def build():
    """Build the application using Nuitka"""

    project_dir = Path(__file__).parent

    # Nuitka build command
    nuitka_args = [
        sys.executable,
        "-m", "nuitka",

        # Output options
        "--standalone",  # Create standalone distribution

        # Application entry point
        "app/main.py",

        # Output naming (kurzer Name für Windows-Pfadlängen-Limit)
        "--output-filename=FreizeitApp",
        "--output-dir=dist",

        # Include data files (templates, static files)
        f"--include-data-dir={project_dir}/app/templates=app/templates",
        f"--include-data-dir={project_dir}/app/static=app/static",

        # Include package data - EXPLIZIT statt --follow-imports
        "--include-package=app",
        "--include-package=fastapi",
        "--include-package=uvicorn",
        "--include-package=sqlalchemy",
        "--include-package=pydantic",
        "--include-package=webview",
        "--include-package=jinja2",
        "--include-package=reportlab",
        "--include-package=openpyxl",
        "--include-package=starlette",
        "--include-package=pydantic_core",

        # WICHTIG: --follow-imports ENTFERNT!
        # Stattdessen explizite Ausschlüsse:

        # Webview Plattformen ausschließen (nur Windows wird benötigt)
        "--nofollow-import-to=webview.platforms.android",
        "--nofollow-import-to=webview.platforms.gtk",
        "--nofollow-import-to=webview.platforms.cocoa",
        "--nofollow-import-to=webview.platforms.qt",

        # ReportLab Test-Module
        "--nofollow-import-to=reportlab.lib.testutils",
        "--nofollow-import-to=reportlab.graphics.testshapes",

        # SQLAlchemy: Nur SQLite wird benötigt - andere Dialekte ausschließen
        "--nofollow-import-to=sqlalchemy.dialects.postgresql",
        "--nofollow-import-to=sqlalchemy.dialects.mysql",
        "--nofollow-import-to=sqlalchemy.dialects.oracle",
        "--nofollow-import-to=sqlalchemy.dialects.mssql",
        "--nofollow-import-to=sqlalchemy.dialects.firebird",
        "--nofollow-import-to=sqlalchemy.dialects.sybase",
        "--nofollow-import-to=sqlalchemy.ext.mypy",

        # DNS & Email-Validation (verursacht Crash bei Kompilierung)
        "--nofollow-import-to=dns",
        "--nofollow-import-to=dns.resolver",
        "--nofollow-import-to=email_validator",

        # Andere nicht benötigte Module
        "--nofollow-import-to=numpy",
        "--nofollow-import-to=pandas",
        "--nofollow-import-to=scipy",
        "--nofollow-import-to=matplotlib",
        "--nofollow-import-to=pytest",
        "--nofollow-import-to=IPython",
        "--nofollow-import-to=jupyter",

        # Optimization - RAM sparen und Stabilität
        "--lto=no",  # Link Time Optimization aus für Stabilität
        "--jobs=1",  # Nur 1 Thread für maximale Stabilität (verhindert Race Conditions)
        "--remove-output",  # Temporäre Dateien löschen
    ]

    # Windows-specific options
    if sys.platform == "win32":
        nuitka_args.extend([
            "--windows-console-mode=disable",
            "--windows-icon-from-ico=app/static/icon.ico",
            "--windows-company-name=Freizeit Rezepturverwaltung",
            "--windows-product-name=Freizeit Rezepturverwaltung",
            "--windows-file-version=1.0.0",
            "--windows-product-version=1.0.0",
        ])

    # Linux-specific options
    elif sys.platform.startswith("linux"):
        nuitka_args.extend([
            "--linux-icon=app/static/icon.png",
        ])

    # macOS-specific options
    elif sys.platform == "darwin":
        nuitka_args.extend([
            "--macos-create-app-bundle",
            "--macos-app-icon=app/static/icon.icns",
            "--macos-app-name=FreizeitRezepturverwaltung",
        ])

    print("=" * 70)
    print("Building Freizeit Rezepturverwaltung with Nuitka")
    print("=" * 70)
    print(f"Project directory: {project_dir}")
    print(f"Platform: {sys.platform}")
    print()
    print("Build-Optionen:")
    print(f"  - Jobs: 1 (maximale Stabilität)")
    print(f"  - LTO: Nein (für Stabilität)")
    print(f"  - DNS-Module: Ausgeschlossen (verhindert Crash)")
    print(f"  - Output: FreizeitApp.exe (kurzer Name)")
    print()

    # Run Nuitka
    try:
        result = subprocess.run(nuitka_args, check=True)
        print()
        print("=" * 70)
        print("✓ Build successful!")
        print("=" * 70)
        print(f"Output directory: {project_dir / 'dist'}")
        return 0
    except subprocess.CalledProcessError as e:
        print()
        print("=" * 70)
        print("✗ Build failed!")
        print("=" * 70)
        print(f"Error: {e}")
        print()
        print("Mögliche Lösungen:")
        print("  1. Schließen Sie andere Programme (mehr RAM freigeben)")
        print("  2. Führen Sie den Build erneut aus (manchmal hilft das)")
        print("  3. Verwenden Sie --jobs=1 für noch weniger RAM-Nutzung")
        return 1
    except FileNotFoundError:
        print()
        print("=" * 70)
        print("✗ Nuitka not found!")
        print("=" * 70)
        print("Please install Nuitka first:")
        print("  pip install nuitka")
        return 1

if __name__ == "__main__":
    sys.exit(build())
