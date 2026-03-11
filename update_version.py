#!/usr/bin/env python3
"""
Versionsverwaltungs-Skript für Kuechenplaner

Dieses Skript hilft bei der Verwaltung der Versionsnummer:
1. Version in version.txt schreiben
2. Git-Tag erstellen
3. GitHub Release erstellen (optional mit Installer-Upload)

Verwendung:
    python update_version.py                 # Zeigt aktuelle Version
    python update_version.py from-git        # Liest Version aus letztem Git-Tag
    python update_version.py 1.2.3           # Setzt Version, erstellt Tag + Release
    python update_version.py 1.2.3 --no-tag  # Setzt nur Version, kein Tag/Release
    python update_version.py 1.2.3 --no-release  # Setzt Version + Tag, kein Release

Voraussetzungen:
    - git muss installiert und konfiguriert sein
    - gh (GitHub CLI) muss installiert und authentifiziert sein (für Releases)
      Installation: https://cli.github.com/
"""

import sys
import subprocess
import glob as globmod
from pathlib import Path
import re

# Pfade
PROJECT_ROOT = Path(__file__).parent
VERSION_FILE = PROJECT_ROOT / "version.txt"
INSTALLER_DIR = PROJECT_ROOT / "installer"


def get_current_version():
    """Liest die aktuelle Version aus version.txt"""
    try:
        if VERSION_FILE.exists():
            return VERSION_FILE.read_text().strip()
        else:
            return "0.0.0"
    except Exception as e:
        print(f"Fehler beim Lesen der version.txt: {e}")
        return "0.0.0"


def get_latest_git_tag():
    """Holt den neuesten Git-Tag"""
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=True
        )
        tag = result.stdout.strip()
        # Entferne 'v' prefix falls vorhanden
        if tag.startswith('v'):
            tag = tag[1:]
        return tag
    except subprocess.CalledProcessError:
        print("Kein Git-Tag gefunden")
        return None
    except Exception as e:
        print(f"Fehler beim Abrufen des Git-Tags: {e}")
        return None


def validate_version(version):
    """Validiert das Versionsformat (Semantic Versioning)"""
    pattern = r'^\d+\.\d+\.\d+(-[a-zA-Z0-9.]+)?$'
    if not re.match(pattern, version):
        print(f"Ungueltiges Versionsformat: {version}")
        print("   Erwartet: MAJOR.MINOR.PATCH (z.B. 1.2.3 oder 1.2.3-beta.1)")
        return False
    return True


def set_version(version):
    """Schreibt die Version in version.txt"""
    try:
        VERSION_FILE.write_text(version + "\n")
        print(f"Version in version.txt gesetzt: {version}")
        return True
    except Exception as e:
        print(f"Fehler beim Schreiben der version.txt: {e}")
        return False


def create_git_tag(version):
    """Erstellt einen Git-Tag fuer die Version"""
    tag_name = f"v{version}"
    try:
        # Prüfe ob Tag bereits existiert
        result = subprocess.run(
            ["git", "tag", "-l", tag_name],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        if result.stdout.strip():
            print(f"Git-Tag {tag_name} existiert bereits")
            return False

        # Erstelle Tag
        subprocess.run(
            ["git", "tag", "-a", tag_name, "-m", f"Release {version}"],
            cwd=PROJECT_ROOT,
            check=True
        )
        print(f"Git-Tag erstellt: {tag_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Fehler beim Erstellen des Git-Tags: {e}")
        return False


def check_gh_cli():
    """Prueft ob GitHub CLI (gh) installiert und authentifiziert ist"""
    try:
        subprocess.run(
            ["gh", "auth", "status"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=True
        )
        return True
    except FileNotFoundError:
        print("GitHub CLI (gh) ist nicht installiert.")
        print("   Installation: https://cli.github.com/")
        return False
    except subprocess.CalledProcessError:
        print("GitHub CLI ist nicht authentifiziert.")
        print("   Bitte ausfuehren: gh auth login")
        return False


def find_installer_files(version):
    """Sucht Installer-Dateien im installer/ Ordner"""
    if not INSTALLER_DIR.exists():
        return []

    # Suche nach Installer-Dateien fuer diese Version
    patterns = [
        str(INSTALLER_DIR / f"FreizeitRezepturverwaltung-Setup-{version}*.exe"),
    ]

    files = []
    for pattern in patterns:
        files.extend(globmod.glob(pattern))

    # Falls keine versionsspezifischen Dateien, suche nach allen .exe im Ordner
    if not files:
        all_exe = globmod.glob(str(INSTALLER_DIR / "*.exe"))
        if all_exe:
            print(f"Keine Installer fuer Version {version} gefunden, aber {len(all_exe)} .exe Datei(en) im installer/ Ordner:")
            for f in all_exe:
                print(f"   - {Path(f).name}")

    return files


def create_github_release(version, installer_files=None):
    """Erstellt ein GitHub Release und laedt optional Installer hoch"""
    tag_name = f"v{version}"

    if not check_gh_cli():
        return False

    try:
        # Release erstellen
        cmd = [
            "gh", "release", "create", tag_name,
            "--title", f"Release {version}",
            "--notes", f"Release Version {version}",
        ]

        # Installer-Dateien als Assets anhaengen
        if installer_files:
            for f in installer_files:
                cmd.append(f)

        subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            check=True
        )

        print(f"GitHub Release erstellt: {tag_name}")
        if installer_files:
            print(f"   {len(installer_files)} Datei(en) hochgeladen:")
            for f in installer_files:
                print(f"   - {Path(f).name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Fehler beim Erstellen des GitHub Releases: {e}")
        return False


def push_tag(version):
    """Pusht den Tag zum Remote"""
    tag_name = f"v{version}"
    try:
        subprocess.run(
            ["git", "push", "origin", tag_name],
            cwd=PROJECT_ROOT,
            check=True
        )
        print(f"Tag gepusht: {tag_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Fehler beim Pushen des Tags: {e}")
        return False


def main():
    if len(sys.argv) == 1:
        # Keine Argumente: Zeige aktuelle Version
        current = get_current_version()
        print(f"Aktuelle Version: {current}")
        print()
        print("Verwendung:")
        print("  python update_version.py from-git           # Version aus Git-Tag uebernehmen")
        print("  python update_version.py 1.2.3              # Version setzen + Tag + Release")
        print("  python update_version.py 1.2.3 --no-tag     # Nur Version setzen")
        print("  python update_version.py 1.2.3 --no-release # Version + Tag, kein Release")
        return

    command = sys.argv[1]

    if command == "from-git":
        # Version aus Git-Tag lesen
        tag_version = get_latest_git_tag()
        if tag_version:
            current = get_current_version()
            if tag_version == current:
                print(f"Version ist bereits aktuell: {current}")
            else:
                if set_version(tag_version):
                    print(f"Version aktualisiert: {current} -> {tag_version}")
        else:
            print("Kein Git-Tag gefunden, kann Version nicht aktualisieren")
            print("Erstelle zuerst einen Tag: python update_version.py 1.0.0")

    else:
        # Neue Version setzen
        new_version = command
        create_tag = "--no-tag" not in sys.argv
        create_release = "--no-release" not in sys.argv and create_tag

        if not validate_version(new_version):
            sys.exit(1)

        current = get_current_version()
        print(f"Aktuelle Version: {current}")
        print(f"Neue Version: {new_version}")
        print()

        # 1. Version in version.txt setzen
        if not set_version(new_version):
            sys.exit(1)

        if not create_tag:
            print()
            print("Version erfolgreich aktualisiert (ohne Git-Tag)")
            print(f"Naechster Schritt: git add version.txt && git commit -m 'Bump version to {new_version}'")
            return

        # 2. Git-Tag erstellen
        tag_ok = create_git_tag(new_version)
        if not tag_ok:
            print()
            print("Version wurde gesetzt, aber Tag-Erstellung fehlgeschlagen")
            return

        # 3. Tag pushen
        print()
        push_ok = push_tag(new_version)
        if not push_ok:
            print(f"Tag manuell pushen: git push origin v{new_version}")

        # 4. GitHub Release erstellen
        if create_release:
            print()
            installer_files = find_installer_files(new_version)
            if installer_files:
                print(f"Installer gefunden: {', '.join(Path(f).name for f in installer_files)}")
            else:
                print("Kein Installer im installer/ Ordner gefunden - Release wird ohne Dateien erstellt")

            release_ok = create_github_release(new_version, installer_files)
            if not release_ok:
                print(f"Release manuell erstellen: gh release create v{new_version}")

        print()
        print("Fertig!")
        print("Naechste Schritte:")
        print(f"   1. git add version.txt && git commit -m 'Bump version to {new_version}'")
        print(f"   2. git push")


if __name__ == "__main__":
    main()
