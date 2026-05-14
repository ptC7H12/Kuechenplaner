---
name: create-release
description: >-
  Startet mit Commit-Check: offene Änderungen werden auf dem aktuellen Branch
  zusammengefasst und committed. Danach Release-Workflow: Feature-Branch in main
  mergen, main pushen, GitHub-Release mit version.txt inkl. Tag und passender
  Setup-EXE aus installer/. Nutzen bei Release, Tag, version.txt, main mergen,
  Installer oder create-release.
disable-model-invocation: true
---

# create-release (Merge → Push → Tag → GitHub-Release)

## GitHub CLI: „Über den Skill bedienen“

Der Skill ist eine Arbeitsanweisung für den **Cursor-Agenten**. Es gibt keine separate GitHub-Anbindung im Skill — der Agent **führt dieselben `gh`-Kommandos in deiner Shell aus**, die du sonst selbst eingeben würdest (Merge/Push/Tag wie `git`, Release und **Upload** wie `gh`).

**Upload nur der passenden Installer-EXE mit `gh`:**

- Zuerst die **eine oder wenigen** passenden Dateien unter `installer/` ermitteln (siehe unten „Installer auswählen“), dann **nur diese Pfade** an `gh` übergeben — **nicht** den ganzen Ordner hochladen.
- **Neues Release:**  
  `gh release create <TAG> --title "…" --generate-notes <pfad/zur/Setup….exe> [weitere passende exes…]`
- **Release existiert schon, nur Asset(s) nachladen/ersetzen:**  
  `gh release upload <TAG> <pfad/zur/Setup….exe> --clobber`

Voraussetzung: `gh` installiert und authentifiziert (`gh auth status`). Fehlt `gh` oder die Anmeldung, der Agent **nicht** raten — Nutzer mit klarer Meldung auf Installation/Login verweisen.

## Kurzantwort: „Geht das so?“

Ja. Zuerst wird der Git-Stand geprüft und bei Bedarf alles Relevante committed; danach wie üblich mergen, `main` pushen, Version/Tag/Release mit passender **`.exe` aus `installer/`**. Voraussetzungen: getesteter Build, `gh` installiert und bei GitHub angemeldet, Remote `origin` zeigt auf GitHub.

## Voraussetzungen

- Nutzer hat Builds **bereits** getestet (kein Ersatz für CI/Tests im Skill).
- Nach Schritt „Commit-Check“ ist der Arbeitsbaum committed (keine offenen Änderungen mehr), außer der Skill bricht vorher ab.
- Projektroot: `version.txt` (eine Zeile, Semver `MAJOR.MINOR.PATCH`).
- Unter **`installer/`** liegen fertige **`.exe`**-Dateien; im Dateinamen steckt die **Versionsnummer** (zum Abgleich mit `version.txt`).
- Tag-Name wie im Projekt zu `new-version`: **`v` + Version** (z. B. `1.3.0` → Tag `v1.3.0`).
- [GitHub CLI](https://cli.github.com/) `gh` verfügbar: `gh auth status` muss OK sein.

## Installer auswählen (Version = Inhalt von `version.txt`, getrimmt)

1. `VERSION` aus `version.txt` lesen (z. B. `1.3.0`).
2. Im Ordner **`installer/`** alle `.exe` finden, die **zu dieser Version passen**.

**Konkret in diesem Repository** (gleiche Logik wie `find_installer_files` in `update_version.py`):  
Glob-Muster `installer/FreizeitRezepturverwaltung-Setup-<VERSION>*.exe` (Beispiel für `1.3.0`: `FreizeitRezepturverwaltung-Setup-1.3.0*.exe`).

**Allgemein**, falls sich das Namensschema ändert: Dateiname muss die Semver-Zeichenkette `VERSION` enthalten (z. B. `…-1.3.0-setup.exe`), und es muss eindeutig klar sein, welche Datei zum Release gehört.

**Treffer:**

- **Genau eine** passende `.exe` → diese an `gh` anhängen.
- **Mehrere** (z. B. unterschiedliche Suffixe nach der Version) → **alle** mit diesem Versionsbezug anhängen, **oder** kurz beim Nutzer nachfragen, welche gemeint ist — nicht wahllos eine wählen.
- **Keine** passende `.exe` → **Stopp**: vorhandene Dateien in `installer/` auflisten, Hinweis auf erwartetes Namensschema / erneuten Build.

## Wichtige Randfälle

- **Commit-Check:** Kein automatischer Commit während **laufendem Merge/Rebase** mit Konflikten oder unvollendetem Index — **Stopp**, Nutzer muss zuerst aufräumen. Keine Secrets oder generierte Artefakte bewusst umgehen: nur Dateien, die Git normalerweise mitnimmt (`git add -A` respektiert `.gitignore`).
- **Auf `main` mit offenen Änderungen:** Vor dem Commit kurz hinweisen, dass direkte Commits auf `main` unüblich sind; wenn der Nutzer den Release-Workflow so angestoßen hat, trotzdem committen (oder nach expliziter Nutzerkorrektur nur stoppieren).
- **Existierender Tag gleichen Namens:** „Tag auf die Version heben“ = Tag auf den neuen Commit zeigen: `git tag -f vX.Y.Z` am Release-Commit, dann `git push origin vX.Y.Z --force-with-lease`. Das überschreibt den Tag auf dem Server — nur tun, wenn das Team das so will (Rewriting geteilter History von Tags).
- **Nur Release ohne erneutes Taggen:** Wenn der Tag schon am richtigen Commit sitzt, kein `-f` nötig; nur `gh release create` (oder fehlendes Release nachziehen).
- **Windows/PowerShell:** Pfade mit Leerzeichen in Anführungszeichen; Installer-Pfad als **einzelner** Argument-String an `gh` übergeben. Glob-Beispiel:  
  `Get-ChildItem -Path installer -Filter "FreizeitRezepturverwaltung-Setup-$v*.exe" | ForEach-Object { $_.FullName }`

## Ablauf (Reihenfolge)

1. **Commit-Check (Anfang, auf dem aktuellen Branch)**  
   - `git status` auswerten (und bei Bedarf kurz die Änderungsliste zeigen).  
   - Wenn **Merge/Rebase/Konflikt** oder Git in einem Zustand ist, in dem kein sauberer Commit möglich ist → **Stopp** mit Hinweis.  
   - Wenn Arbeitsbaum **bereits sauber** (nichts zu committen) → mit Schritt 2 weitermachen.  
   - Sonst: alle für Git vorgesehenen Änderungen **stagen**: `git add -A`  
     - Wenn danach **nichts staged** ist (z. B. nur ignorierte Dateien wie große `.exe` geändert) → Nutzer kurz informieren, **keinen** leeren Commit erzwingen; mit Schritt 2 weitermachen, sofern der Rest des Workflows passt.  
     - Andernfalls committen: `git commit -m "chore: Arbeitsstand vor Release"` (Message nach Projektkonvention anpassbar, Hauptsache eindeutig und neutral.)  
   - Nach **erfolgreichem Commit** (wenn einer erstellt wurde): optional `git push origin <aktueller-branch>`, damit der Merge auf `main` nicht nur lokale Commits zieht — **wenn** der Feature-Branch schon ein Remote-Tracking-Branch ist; sonst Nutzer kurz informieren.

2. **Aktuellen Branch merken** (Feature-/Release-Branch, **nicht** `main`):  
   `FEATURE=$(git rev-parse --abbrev-ref HEAD)`  
   Wenn bereits `main`: Nutzer fragen, welcher Branch gemerged werden soll, oder ob nur Tag/Release nachgezogen werden soll.

3. **`main` aktualisieren und mergen**  
   - `git fetch origin`  
   - `git checkout main`  
   - `git pull origin main`  
   - `git merge --no-ff "$FEATURE"` (oder nach Teamkonvention `--ff-only` / Squash — Standard hier: expliziter Merge mit `--no-ff`, außer Nutzer widerspricht)  
   - Bei Merge-Konflikten: **Stopp**, Konflikte lösen, nicht blind pushen.

4. **Optional: Tests/Build noch einmal**  
   Nur wenn Nutzer oder Projekt das verlangt; sonst „getestet“ aus Voraussetzungen vertrauen.

5. **`main` pushen**  
   `git push origin main`  
   Nur wenn Merge und ggf. Checks fehlerfrei.

6. **Version lesen**  
   Inhalt von `version.txt` trimmen; muss `MAJOR.MINOR.PATCH` sein.  
   `TAG="v$(cat version.txt | tr -d '\r\n' | xargs)"` (unter Windows entsprechend: PowerShell `Get-Content` trimmen).

7. **Tag am aktuellen `main`-Commit**  
   - Tag fehlt: `git tag -a "$TAG" -m "Release $TAG"` (oder leichtgewichtig ohne `-a` nach Konvention).  
   - Tag existiert und soll „hochgezogen“ werden: `git tag -f "$TAG"` dann Push mit `--force-with-lease` wie oben.

8. **Tags pushen**  
   `git push origin "$TAG"`  
   Bei Force-Tag: `git push origin "$TAG" --force-with-lease`.

9. **Passende Installer-EXE(s) ermitteln**  
   Gemäß Abschnitt „Installer auswählen“; Variable(n) mit vollem Pfad für Schritt 10 merken.

10. **GitHub-Release mit nur diesen EXE(s)**  
   Beispiel (nur Platzhalter — echte Pfade aus Schritt 9):

   ```bash
   gh release create "$TAG" \
     --title "$(cat version.txt | tr -d '\r\n')" \
     --generate-notes \
     "$INSTALLER_EXE"
   ```

   Mehrere passende Dateien: alle `"$INSTALLER_EXE"`-Platzhalter durch die ermittelten Pfade ersetzen (mehrere Argumente hintereinander).

   Wenn das Release schon existiert:  
   `gh release upload "$TAG" "$INSTALLER_EXE" --clobber`

11. **Aufräumen (optional)**  
    Lokal wieder auf Arbeitsbranch wechseln oder `main` lassen — nach Nutzerwunsch.

## Checkliste für den Agenten

- [ ] Commit-Check: `git status`; bei Bedarf `git add -A` + Commit; bei blockiertem Git-Zustand Stopp
- [ ] Feature-Branch ggf. gepusht, falls Remote-Workflow
- [ ] Feature-Branchname gesichert vor `checkout main`
- [ ] `main` gemerged, Konflikte = Stopp
- [ ] `main` gepusht
- [ ] `version.txt` gelesen, `TAG=v…` gesetzt
- [ ] Tag erstellt oder mit Absicht `-f` + `--force-with-lease`
- [ ] Passende `installer/*.exe` zur Version gefunden (0 = Stopp mit Liste)
- [ ] Upload: `gh release create …` **nur mit den ermittelten EXE-Pfaden** **oder** `gh release upload … --clobber`

## Bezug zu `new-version`

Versionierung auf neuem Branch (`new-version`-Skill) und Abschluss-Release (`create-release`) sind getrennt: Typischerweise steht die finale `version.txt` bereits auf dem Branch, der nach `main` gemerged wird; dieser Skill **bumpt** `version.txt` nicht automatisch.

## Bezug zu `update_version.py`

Die Auswahl der Installer-Dateien ist mit `find_installer_files` in `update_version.py` abgestimmt; bei Abweichungen im Namensschema zuerst dieses Skript bzw. den Build prüfen, dann den Abschnitt „Installer auswählen“ im Skill anpassen.
