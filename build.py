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
        "--onefile",     # Pack everything into single executable

        # Application entry point
        "app/main.py",

        # Output naming
        "--output-dir=dist",
        "--output-filename=FreizeitRezepturverwaltung",

        # Include data files (templates, static files)
        f"--include-data-dir={project_dir}/app/templates=app/templates",
        f"--include-data-dir={project_dir}/app/static=app/static",

        # Include package data
        "--include-package=app",
        "--include-package=fastapi",
        "--include-package=uvicorn",
        "--include-package=sqlalchemy",
        "--include-package=pydantic",
        # webview is handled by pywebview plugin automatically
        "--include-package=jinja2",
        "--include-package=reportlab",
        "--include-package=openpyxl",

        # Enable plugins
        "--enable-plugin=pylint-warnings",
        "--enable-plugin=pywebview",  # Explicitly enable pywebview plugin

        # Follow imports
        "--follow-imports",

        # Optimization
        "--lto=yes",  # Link Time Optimization

        # Platform-specific options
    ]

    # Windows-specific options
    if sys.platform == "win32":
        nuitka_args.extend([
            "--windows-disable-console",  # No console window
            "--windows-icon-from-ico=app/static/icon.ico",  # Application icon (if exists)
            "--windows-company-name=Freizeit Rezepturverwaltung",
            "--windows-product-name=Freizeit Rezepturverwaltung",
            "--windows-file-version=1.0.0",
            "--windows-product-version=1.0.0",
        ])

    # Linux-specific options
    elif sys.platform.startswith("linux"):
        nuitka_args.extend([
            "--linux-icon=app/static/icon.png",  # Application icon (if exists)
        ])

    # macOS-specific options
    elif sys.platform == "darwin":
        nuitka_args.extend([
            "--macos-create-app-bundle",
            "--macos-app-icon=app/static/icon.icns",  # Application icon (if exists)
            "--macos-app-name=FreizeitRezepturverwaltung",
        ])

    print("=" * 70)
    print("Building Freizeit Rezepturverwaltung with Nuitka")
    print("=" * 70)
    print(f"Project directory: {project_dir}")
    print(f"Platform: {sys.platform}")
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
