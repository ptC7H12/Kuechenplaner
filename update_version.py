#!/usr/bin/env python3
"""
Versionsverwaltungs-Skript für Kuechenplaner

Dieses Skript hilft bei der Verwaltung der Versionsnummer:
1. Version in version.txt schreiben
2. Aenderung committen
3. Git-Tag erstellen und pushen
4. GitHub Release erstellen (optional mit Installer-Upload)

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


def run_git(*args):
    """Fuehrt einen Git-Befehl aus und gibt das Ergebnis zurueck"""
    result = subprocess.run(
        ["git"] + list(args),
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    return result


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
    result = run_git("describe", "--tags", "--abbrev=0")
    if result.returncode != 0:
        print("Kein Git-Tag gefunden")
        return None
    tag = result.stdout.strip()
    if tag.startswith('v'):
        tag = tag[1:]
    return tag


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
        print(f"[OK] Version in version.txt gesetzt: {version}")
        return True
    except Exception as e:
        print(f"[FEHLER] Schreiben der version.txt: {e}")
        return False


def commit_version(version):
    """Committet die version.txt Aenderung"""
    # Stage version.txt
    result = run_git("add", "version.txt")
    if result.returncode != 0:
        print(f"[FEHLER] git add: {result.stderr}")
        return False

    # Prüfe ob es etwas zu committen gibt
    result = run_git("diff", "--cached", "--quiet")
    if result.returncode == 0:
        print("[INFO] version.txt hat sich nicht geaendert, kein Commit noetig")
        return True

    # Commit
    result = run_git("commit", "-m", f"Bump version to {version}")
    if result.returncode != 0:
        print(f"[FEHLER] git commit: {result.stderr}")
        return False

    print(f"[OK] Commit erstellt: Bump version to {version}")
    return True


def create_git_tag(version):
    """Erstellt einen Git-Tag fuer die Version"""
    tag_name = f"v{version}"

    # Prüfe ob Tag bereits existiert
    result = run_git("tag", "-l", tag_name)
    if result.stdout.strip():
        print(f"[FEHLER] Git-Tag {tag_name} existiert bereits")
        return False

    # Erstelle Tag
    result = run_git("tag", "-a", tag_name, "-m", f"Release {version}")
    if result.returncode != 0:
        print(f"[FEHLER] Tag erstellen: {result.stderr}")
        return False

    print(f"[OK] Git-Tag erstellt: {tag_name}")
    return True


def push_all(version):
    """Pusht Commit und Tag zum Remote"""
    tag_name = f"v{version}"

    # Aktuellen Branch pushen
    result = run_git("push")
    if result.returncode != 0:
        print(f"[FEHLER] git push: {result.stderr}")
        return False
    print("[OK] Commit gepusht")

    # Tag pushen
    result = run_git("push", "origin", tag_name)
    if result.returncode != 0:
        print(f"[FEHLER] Tag push: {result.stderr}")
        return False
    print(f"[OK] Tag gepusht: {tag_name}")
    return True


def check_gh_cli():
    """Prueft ob GitHub CLI (gh) installiert und authentifiziert ist"""
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print("[FEHLER] GitHub CLI ist nicht authentifiziert.")
            print("   Bitte ausfuehren: gh auth login")
            return False
        return True
    except FileNotFoundError:
        print("[FEHLER] GitHub CLI (gh) ist nicht installiert.")
        print("   Installation: https://cli.github.com/")
        return False


def find_installer_files(version):
    """Sucht Installer-Dateien im installer/ Ordner"""
    if not INSTALLER_DIR.exists():
        return []

    # Suche nach Installer-Dateien fuer diese Version
    pattern = str(INSTALLER_DIR / f"FreizeitRezepturverwaltung-Setup-{version}*.exe")
    files = globmod.glob(pattern)

    # Falls keine versionsspezifischen Dateien, suche nach allen .exe im Ordner
    if not files:
        all_exe = globmod.glob(str(INSTALLER_DIR / "*.exe"))
        if all_exe:
            print(f"[INFO] Keine Installer fuer Version {version} gefunden.")
            print(f"   Gefundene .exe Dateien im installer/ Ordner:")
            for f in all_exe:
                print(f"   - {Path(f).name}")

    return files


def create_github_release(version, installer_files=None):
    """Erstellt ein GitHub Release und laedt optional Installer hoch"""
    tag_name = f"v{version}"

    if not check_gh_cli():
        return False

    try:
        cmd = [
            "gh", "release", "create", tag_name,
            "--title", f"Release {version}",
            "--notes", f"Release Version {version}",
        ]

        # Installer-Dateien als Assets anhaengen
        if installer_files:
            for f in installer_files:
                cmd.append(f)

        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"[FEHLER] GitHub Release: {result.stderr}")
            return False

        print(f"[OK] GitHub Release erstellt: {tag_name}")
        if installer_files:
            for f in installer_files:
                print(f"   Hochgeladen: {Path(f).name}")
        return True
    except Exception as e:
        print(f"[FEHLER] GitHub Release: {e}")
        return False


def main():
    try:
        if len(sys.argv) == 1:
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
            tag_version = get_latest_git_tag()
            if tag_version:
                current = get_current_version()
                if tag_version == current:
                    print(f"Version ist bereits aktuell: {current}")
                else:
                    if set_version(tag_version):
                        print(f"Version aktualisiert: {current} -> {tag_version}")
            else:
                print("Kein Git-Tag gefunden.")
                print("Erstelle zuerst einen Tag: python update_version.py 1.0.0")
            return

        # Neue Version setzen
        new_version = command
        create_tag = "--no-tag" not in sys.argv
        create_release = "--no-release" not in sys.argv and create_tag

        if not validate_version(new_version):
            sys.exit(1)

        current = get_current_version()
        print(f"Aktuelle Version:  {current}")
        print(f"Neue Version:      {new_version}")
        print("=" * 50)

        # Schritt 1: Version in version.txt setzen
        if not set_version(new_version):
            sys.exit(1)

        if not create_tag:
            print()
            print("Fertig! Version aktualisiert (ohne Git-Tag)")
            return

        # Schritt 2: version.txt committen
        if not commit_version(new_version):
            print("[FEHLER] Commit fehlgeschlagen - breche ab")
            sys.exit(1)

        # Schritt 3: Git-Tag erstellen
        if not create_git_tag(new_version):
            print("[FEHLER] Tag-Erstellung fehlgeschlagen - breche ab")
            sys.exit(1)

        # Schritt 4: Commit + Tag pushen
        if not push_all(new_version):
            print()
            print(f"Manuell pushen:")
            print(f"   git push")
            print(f"   git push origin v{new_version}")
        else:
            # Schritt 5: GitHub Release erstellen
            if create_release:
                print("-" * 50)
                installer_files = find_installer_files(new_version)
                if installer_files:
                    print(f"Installer gefunden: {', '.join(Path(f).name for f in installer_files)}")
                else:
                    print("Kein Installer gefunden - Release wird ohne Dateien erstellt")

                if not create_github_release(new_version, installer_files):
                    print(f"Release manuell erstellen: gh release create v{new_version}")

        print("=" * 50)
        print("Fertig!")

    except KeyboardInterrupt:
        print("\nAbgebrochen.")
    except Exception as e:
        print(f"\nUnerwarteter Fehler: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Windows: Fenster offen halten damit man die Ausgabe lesen kann
        if sys.platform == "win32":
            print()
            input("Druecke Enter zum Beenden...")


if __name__ == "__main__":
    main()
