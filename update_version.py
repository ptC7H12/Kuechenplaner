#!/usr/bin/env python3
"""
Versionsverwaltungs-Skript für Kuechenplaner

Dieses Skript hilft bei der Verwaltung der Versionsnummer:
1. Version aus Git-Tag auslesen und in version.txt schreiben
2. Neue Version setzen und Git-Tag erstellen

Verwendung:
    python update_version.py                 # Zeigt aktuelle Version
    python update_version.py from-git        # Liest Version aus letztem Git-Tag
    python update_version.py 1.2.3           # Setzt neue Version und erstellt Tag
    python update_version.py 1.2.3 --no-tag  # Setzt nur Version, kein Git-Tag
"""

import sys
import subprocess
from pathlib import Path
import re

# Pfade
PROJECT_ROOT = Path(__file__).parent
VERSION_FILE = PROJECT_ROOT / "version.txt"


def get_current_version():
    """Liest die aktuelle Version aus version.txt"""
    try:
        if VERSION_FILE.exists():
            return VERSION_FILE.read_text().strip()
        else:
            return "0.0.0"
    except Exception as e:
        print(f"❌ Fehler beim Lesen der version.txt: {e}")
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
        print("⚠️  Kein Git-Tag gefunden")
        return None
    except Exception as e:
        print(f"❌ Fehler beim Abrufen des Git-Tags: {e}")
        return None


def validate_version(version):
    """Validiert das Versionsformat (Semantic Versioning)"""
    pattern = r'^\d+\.\d+\.\d+(-[a-zA-Z0-9.]+)?$'
    if not re.match(pattern, version):
        print(f"❌ Ungültiges Versionsformat: {version}")
        print("   Erwartet: MAJOR.MINOR.PATCH (z.B. 1.2.3 oder 1.2.3-beta.1)")
        return False
    return True


def set_version(version):
    """Schreibt die Version in version.txt"""
    try:
        VERSION_FILE.write_text(version + "\n")
        print(f"✅ Version in version.txt gesetzt: {version}")
        return True
    except Exception as e:
        print(f"❌ Fehler beim Schreiben der version.txt: {e}")
        return False


def create_git_tag(version):
    """Erstellt einen Git-Tag für die Version"""
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
            print(f"⚠️  Git-Tag {tag_name} existiert bereits")
            return False

        # Erstelle Tag
        subprocess.run(
            ["git", "tag", "-a", tag_name, "-m", f"Release {version}"],
            cwd=PROJECT_ROOT,
            check=True
        )
        print(f"✅ Git-Tag erstellt: {tag_name}")
        print(f"💡 Zum Pushen: git push origin {tag_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Fehler beim Erstellen des Git-Tags: {e}")
        return False


def main():
    if len(sys.argv) == 1:
        # Keine Argumente: Zeige aktuelle Version
        current = get_current_version()
        print(f"📌 Aktuelle Version: {current}")
        print()
        print("Verwendung:")
        print("  python update_version.py from-git        # Version aus Git-Tag übernehmen")
        print("  python update_version.py 1.2.3           # Neue Version setzen und Tag erstellen")
        print("  python update_version.py 1.2.3 --no-tag  # Nur Version setzen, kein Tag")
        return

    command = sys.argv[1]

    if command == "from-git":
        # Version aus Git-Tag lesen
        tag_version = get_latest_git_tag()
        if tag_version:
            current = get_current_version()
            if tag_version == current:
                print(f"✅ Version ist bereits aktuell: {current}")
            else:
                if set_version(tag_version):
                    print(f"📌 Version aktualisiert: {current} → {tag_version}")
        else:
            print("❌ Kein Git-Tag gefunden, kann Version nicht aktualisieren")
            print("💡 Erstelle zuerst einen Tag: python update_version.py 1.0.0")

    else:
        # Neue Version setzen
        new_version = command
        create_tag = "--no-tag" not in sys.argv

        if not validate_version(new_version):
            sys.exit(1)

        current = get_current_version()
        print(f"📌 Aktuelle Version: {current}")
        print(f"📌 Neue Version: {new_version}")

        if not set_version(new_version):
            sys.exit(1)

        if create_tag:
            if create_git_tag(new_version):
                print()
                print("✅ Version erfolgreich aktualisiert!")
                print("📝 Nächste Schritte:")
                print(f"   1. Änderungen committen: git add version.txt && git commit -m 'Bump version to {new_version}'")
                print(f"   2. Tag pushen: git push origin v{new_version}")
            else:
                print()
                print("⚠️  Version wurde gesetzt, aber Tag-Erstellung fehlgeschlagen")
        else:
            print()
            print("✅ Version erfolgreich aktualisiert (ohne Git-Tag)")
            print("📝 Nächster Schritt:")
            print(f"   git add version.txt && git commit -m 'Bump version to {new_version}'")


if __name__ == "__main__":
    main()
