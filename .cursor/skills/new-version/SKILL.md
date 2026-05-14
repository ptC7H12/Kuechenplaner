---
name: new-version
description: >-
  Erhöht die Minor-Version in version.txt (Semver) und erstellt einen lokalen Git-Branch
  benannt wie die neue Version, wenn der aktuelle Branch main ist; bei einem Branch,
  der bereits wie eine Versionsnummer heißt, keine Änderung. Nutzen wenn der Benutzer
  NewVersion, Minor-Bump, version.txt, Release-Branch oder Versionsbranch sagt.
disable-model-invocation: true
---

# NewVersion (Git + version.txt)

## Annahme zur Formulierung

Punkt 1 ist so umgesetzt: **Nur wenn der aktuelle Branch `main` ist**, Minor erhöhen und neuen Branch anlegen. („Wenn nicht main …“ würde ungewollt auf Feature-Branches versionieren.) Wenn du stattdessen wirklich „nur wenn nicht main“ meinst, Skill-Text anpassen.

## Voraussetzungen

- Repository hat `version.txt` im **Projektwurzel**-Verzeichnis (eine Zeile, Semver `MAJOR.MINOR.PATCH`, wie in diesem Projekt).
- Standard-Branch heißt **`main`** (nicht `master` — bei `master` Skill oder Remote-Default prüfen).

## Versions-Branch erkennen

Der aktuelle Branch ist **bereits ein Versions-Branch** (dann **nichts tun**), wenn der Name zu Semver passt:

- `^\d+\.\d+\.\d+` (z. B. `1.3.0`), oder
- `^v\d+\.\d+\.\d+` (z. B. `v1.3.0`)

Optional mit Suffix `-…` (Pre-Release), falls ihr das für Branches nutzt: `^\d+\.\d+\.\d+(-[a-zA-Z0-9.]+)?$` bzw. mit führendem `v`.

## Ablauf

1. Aktuellen Branch ermitteln: `git rev-parse --abbrev-ref HEAD`.
2. **Wenn** der Branch dem Versionsmuster entspricht → **Stopp** (keine Änderung, kurz mitteilen).
3. **Wenn** der Branch **nicht** `main` ist → **Stopp** (keine automatische Versionierung; Nutzer auf `main` verweisen), außer die Nutzeranweisung explizit erweitert den Ablauf.
4. **Wenn** der Branch `main` ist:
   - `version.txt` lesen, trimmen, gültiges `MAJOR.MINOR.PATCH` prüfen.
   - Neue Version: **Minor + 1**, **Patch = 0** (Beispiel: `1.2.0` → `1.3.0`).
   - Prüfen, ob der lokale Branch **`v<neue-version>`** schon existiert; wenn ja → abbrechen und Hinweis geben.
   - `version.txt` mit der neuen Version schreiben (eine Zeile, abschließender Zeilenumbruch wie bisher).
   - Neuen Branch erstellen und auschecken: `git checkout -b v<neue-version>`  
     (Branch-Name = `v` + neue Version, konsistent zu Git-Tags in `update_version.py`.)
   - Änderung committen, sofern gewünscht oder Projektstandard: `git add version.txt` und Commit z. B. `Bump version to <neue-version>`.

## Kurz-Checkliste für den Agenten

- [ ] Branchname geholt
- [ ] Bei Versions-Branch → Ende
- [ ] Bei nicht-`main` → Ende (mit Hinweis)
- [ ] Bei `main` → Minor-Bump + `version.txt` + `git checkout -b vX.Y.Z` (+ Commit nach Konvention)

## Edge Cases

- Arbeitsbaum nicht sauber: Nutzer informieren; nicht blind committen.
- `version.txt` fehlt oder ungültig: abbrechen, Format erklären (`MAJOR.MINOR.PATCH`).
