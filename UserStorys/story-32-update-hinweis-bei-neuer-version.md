# Story 32: Update-Hinweis bei neuer Version (GitHub-Release-Check)

**Status:** Review
**Aufwand:** Klein-Mittel
**Machbarkeit:** Sehr gut
**Implementiert in:** `app/services/update_checker.py`, `app/constants.py:12`, `app/routers/settings.py:119-123`, `app/main.py:40-48,62-65`, `app/templates/base.html:269-303,374-393`, `tests/test_update_check.py`

## Beschreibung

Als Küchenplaner-Nutzer möchte ich automatisch erfahren, wenn eine neuere
Programmversion veröffentlicht wurde, damit ich rechtzeitig aktualisieren kann.
Beim App-Start und danach periodisch (alle 2 Stunden) soll das GitHub-Repository
auf das neueste Release geprüft werden; ist die veröffentlichte Version höher als
die laufende, erscheint ein Toast-Hinweis im bestehenden UI-Stil, der nur über
das ×-Symbol geschlossen wird.

## Ist-Zustand

- `app/routers/settings.py:61-73` — `_read_version()` / `APP_VERSION` liest die lokale `version.txt`; es gibt keinen Abgleich mit veröffentlichten GitHub-Releases.
- `app/constants.py:11` — `REPO_URL = "https://github.com/ptC7H12/Kuechenplaner"`; kein API-/Releases-Endpoint definiert.
- `app/main.py:40-61` — `lifespan` führt Backup, Migrationen und Seeding aus; kein Update-Check beim Start.
- `app/templates/base.html:218-257` — `FreizeitApp.showToast(message, type)` blendet jeden Toast nach 5 s automatisch wieder aus; keine persistente, nur manuell schließbare Variante.
- `app/main.py:164,169` — `urllib.request` wird bereits für den Health-Check verwendet → für den GitHub-Abruf wiederverwendbar; `requests`/`httpx` sind **nicht** in `requirements.txt` enthalten.
- Git-Release-Tags haben das Format `vX.Y.Z` (z. B. `v1.4.0`), die GitHub-API `releases/latest` liefert dies als `tag_name`.

## Akzeptanzkriterien

- [x] Beim App-Start wird einmalig im Hintergrund auf eine neuere Release-Version geprüft, ohne den Start zu blockieren oder bei Fehlern abzubrechen.
- [x] Der Check wiederholt sich periodisch alle 2 Stunden.
- [x] Versionsvergleich: GitHub-`tag_name` (führendes `v` entfernt) wird per Semver gegen `APP_VERSION` verglichen; nur eine echt höhere Version gilt als verfügbares Update.
- [x] Bei verfügbarem Update erscheint ein Toast im bestehenden Toast-Stil, der die neue Version nennt und einen Link zu den Releases (`REPO_URL/releases`) enthält.
- [x] Der Update-Toast blendet sich **nicht** automatisch aus, sondern wird nur über das ×-Symbol geschlossen.
- [x] Ein geschlossener Hinweis erscheint für dieselbe Version nicht erneut (Merkung pro Version via `localStorage`); erst eine noch neuere Version zeigt ihn wieder.
- [x] Fehlende Internetverbindung, GitHub-Fehler oder `APP_VERSION == "unknown"` werden still ignoriert (kein Fehler-Toast, kein Crash).
- [x] GitHub wird höchstens alle 2 h abgefragt (serverseitiger Cache), nicht bei jedem Frontend-Poll.
- [x] Pytest deckt ab: Update verfügbar, kein Update (gleiche/niedrigere Version), Netzwerkfehler ohne Exception, Cache verhindert erneuten Abruf innerhalb des Intervalls.

## Technische Umsetzung (Vorschlag)

### Backend

- Neuer Service `app/services/update_checker.py`:
  - `check_for_update(force=False) -> dict` fragt `https://api.github.com/repos/ptC7H12/Kuechenplaner/releases/latest` per `urllib.request` (mit `User-Agent`-Header, Timeout ~5 s) ab, parst `tag_name`, entfernt führendes `v` und vergleicht per Semver-Tupel gegen `APP_VERSION`.
  - Rückgabe z. B. `{"update_available": bool, "current_version": str, "latest_version": str, "release_url": str}`.
  - Modulweiter Cache (Zeitstempel + letztes Ergebnis); erneuter Remote-Abruf nur, wenn älter als 2 h (`UPDATE_CHECK_INTERVAL`) oder `force=True`.
  - Alle Netzwerk-/Parse-Fehler sowie `APP_VERSION == "unknown"` abfangen → `update_available=False`, keine Exception nach außen.
  - API-URL aus `REPO_URL` ableiten bzw. Konstante in `app/constants.py` ergänzen.
- `app/main.py` `lifespan`: initialen Check beim Start anstoßen, ohne den Start zu verzögern (z. B. in einem Daemon-`Thread`, der den Cache befüllt; Fehler werden geloggt, nicht propagiert).
- Neuer Endpoint in `app/routers/settings.py`: `GET /settings/api/update-check` → liefert das gecachte Ergebnis als JSON (`update_available`, `latest_version`, `release_url`). Versionslese-Logik (`APP_VERSION`) wiederverwenden, nicht duplizieren.

### Frontend

- `app/templates/base.html`: `showToast` um eine persistente Variante erweitern (z. B. `showToast(message, type, {persist: true})` bzw. eigene `showUpdateToast`), die das 5-s-Auto-Ausblenden überspringt und nur per ×-Button schließbar ist; Schließen ruft einen Callback zum Merken der Version.
- Kleines JS-Snippet (in `base.html` oder `layout.js`): beim Laden und per `setInterval` alle 2 h `GET /settings/api/update-check` abrufen. Bei `update_available` und sofern `latest_version` nicht in `localStorage` als „dismissed“ markiert ist → persistenten Toast mit deutschem Text (z. B. „Neue Version {latest_version} verfügbar“) und Releases-Link anzeigen. Beim Schließen `localStorage`-Schlüssel pro Version setzen.

### Tests

- `tests/test_update_check.py` (In-Memory-DB / Monkeypatch des GitHub-Abrufs):
  - Höhere Remote-Version → `update_available=True`, korrekte `latest_version`/`release_url`.
  - Gleiche oder niedrigere Version → `update_available=False`.
  - Netzwerkfehler (Monkeypatch wirft) → `update_available=False`, keine Exception.
  - Zweiter Aufruf innerhalb des Intervalls löst keinen erneuten Remote-Abruf aus (Cache greift).
