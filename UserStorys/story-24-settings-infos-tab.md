# Story 24: Einstellungen — Neuer Reiter "Infos" mit Version & Git-Link

**Status:** Done
**Aufwand:** Klein
**Machbarkeit:** Sehr gut
**Implementiert in:** `app/templates/settings/index.html:42-46` (Tab-Button + Sektion), `app/routers/settings.py:64-65` (`app_version` & `repo_url` Context), Version aus `version.txt` angezeigt

## Beschreibung

Als Küchenplaner möchte ich auf der Einstellungen-Seite sehen, welche Version der App ich nutze und einen Link zum Quellcode-Repository haben, damit ich bei Fragen oder Bug-Reports einen Anhaltspunkt habe.

## Ist-Zustand

- `app/templates/settings/index.html:8-41` hat Tabs: `camps`, `units`, `tags`, `import`, `backup`
- Version `1.4.0` steht nur in `version.txt` — wird aktuell nirgends im Frontend angezeigt
- Kein Git-Repo-Link in der App

## Akzeptanzkriterien

- [x] Neuer Tab "Infos" rechts am Ende der Tab-Leiste in `settings/index.html`
- [x] Tab zeigt: Programm-Version (aus `version.txt`), Link zum Git-Repository
- [x] Optional: Build-Datum, Python-Version, Lizenz, kurze App-Beschreibung
- [x] Styling konsistent mit den anderen Tab-Inhalten (bestehende `.card`-Klassen)
- [x] Git-Repo-URL wird konfigurierbar gehalten (z.B. via Environment-Variable oder Konstante)

## Technische Umsetzung

- Version-Loader: kleine Helper-Funktion `get_app_version()` in `app/main.py` oder neues `app/utils/version.py`, die `version.txt` einliest und cached
- Settings-Router um Kontext `app_version` und `repo_url` erweitern
- Repo-URL als Konstante in `app/constants.py` (z.B. `REPO_URL = "https://github.com/..."`) — falls die echte URL bekannt ist, dort eintragen; sonst Placeholder
- Tab-Button in `settings/index.html:8-41` ergänzen (`infos`)
- Neuer Tab-Content-Bereich (analog zu den bestehenden) — ggf. als Include-Partial `templates/settings/_tab_infos.html`
