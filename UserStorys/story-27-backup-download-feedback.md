# Story 27: Backup-Download — Feedback, Uhrzeit im Dateinamen, Pfad-Anzeige

**Status:** Done
**Aufwand:** Klein-Mittel
**Machbarkeit:** Gut

## Beschreibung

Als Küchenplaner möchte ich beim Backup meiner Datenbank
- eine Rückmeldung über Erfolg/Fehlschlag bekommen (Toast),
- mehrere Backups am selben Tag erzeugen können (Uhrzeit im Dateinamen),
- erkennen können, ob ein Backup automatisch oder manuell erzeugt wurde (Trigger-Suffix),
- jederzeit nachsehen können, wo die Backup-Dateien liegen (Pfad im UI + Kopier-Button),

damit ich Backups gezielt und nachvollziehbar managen kann.

## Ist-Zustand

- `app/templates/settings/index.html:377-382` — Button "Backup herunterladen" hat weder `hx-*`, `onclick` noch `href`. Klick → nichts passiert, kein Feedback.
- `app/routers/settings.py` — kein Download-Endpoint vorhanden.
- `app/database.py:144` — Auto-Backup-Dateiname `app_{date.today().isoformat()}.db`. Wegen `if not backup_path.exists()` (Zeile 145) gibt es **nur ein Backup pro Tag**.
- `app/database.py:157-163` — Cleanup behält die letzten 7 Auto-Backups (`app_*.db`).
- Speicherort `<DATA_DIR>/backups/` (Windows: `%APPDATA%/KuechenApp/backups/`) wird im UI nirgends angezeigt. Der Nutzer kennt seinen Backup-Pfad nicht.
- Toast-Helper steht global zur Verfügung: `FreizeitApp.showToast(message, type)` in `app/templates/base.html:219` mit Typen `success`/`error`/`warning`/`info`.

## Akzeptanzkriterien

- [ ] Klick auf "Backup herunterladen" startet den Download einer aktuellen `.db`-Datei.
- [ ] Toast erscheint nach erfolgreichem Download (`success`) bzw. bei Fehler (`error`).
- [ ] Datei-Suffix enthält `_manual` bei manuellem Download, `_auto` beim Auto-Backup. Format: `app_YYYY-MM-DD_HHMMSS_<auto|manual>.db` (Beispiel: `app_2026-05-17_143015_manual.db`).
- [ ] Dateiname enthält Datum **und** Uhrzeit → mehrere Backups am selben Tag möglich.
- [ ] Im Backup-Tab steht der absolute Backup-Pfad sichtbar (monospaced) mit Kopier-Button. Klick auf Kopier-Button → Pfad im Clipboard + Toast "Pfad kopiert".
- [ ] Auto-Backup-Cleanup löscht weiterhin nur Auto-Backups (max. 7), keine manuellen Backups.
- [ ] Bestehende Backups im alten Namensschema (`app_YYYY-MM-DD.db`) verursachen keine Fehler beim Cleanup oder Listing.
- [ ] Pytest deckt ab: (a) Endpoint liefert `FileResponse` mit korrektem Filename, (b) Filename-Format ist parsebar (Trigger erkennbar), (c) Cleanup respektiert `_manual` vs. `_auto`.

## Technische Umsetzung (Vorschlag)

**Backend:**

- `app/database.py:133-164` — `backup_database(trigger: str = "auto") -> Path` erweitern:
  - Dateiname: `app_{datetime.now().strftime("%Y-%m-%d_%H%M%S")}_{trigger}.db`.
  - `if not backup_path.exists()`-Check entfernen (für `manual`) bzw. auf "ein Auto-Backup pro Tag" umstellen (`app_{date.today().isoformat()}_*_auto.db` per Glob prüfen).
  - Cleanup-Glob auf `app_*_auto.db` einschränken → manuelle Backups bleiben erhalten.
  - Rückgabe: Pfad zur erstellten Datei (für den Endpoint).
- `app/routers/settings.py` — neuer Endpoint:
  ```python
  @router.get("/database/download")
  def download_database():
      path = backup_database(trigger="manual")
      return FileResponse(path, filename=path.name, media_type="application/octet-stream")
  ```
- Pfad in Template-Context geben: `backup_dir = str(DATA_DIR / "backups")`.

**Frontend:**

- `app/templates/settings/index.html:377-382` — Button auf `<a href="{{ url_for('download_database') }}" class="btn btn-primary btn-md" @click="$nextTick(() => FreizeitApp.showToast('Backup wird heruntergeladen…', 'success'))">…</a>` umstellen (oder `hx-get`-Variante mit `htmx:afterRequest`-Hook). Bei `error`: Toast mit `'Backup fehlgeschlagen'`.
- Direkt unter dem Hilfetext (Zeile 373-375): Pfad-Block mit `<code>{{ backup_dir }}</code>` + kleiner Button `Pfad kopieren` (Alpine + `navigator.clipboard.writeText`), bei Erfolg `FreizeitApp.showToast('Pfad kopiert', 'success')`.

**Tests:**

- `tests/test_backup_download.py` — neuer Test mit `TestClient`:
  - GET `/settings/database/download` → `200`, `Content-Disposition: attachment; filename=app_*_manual.db`.
  - Erzeugte Datei existiert im `backups/`-Ordner und ist eine valide SQLite-Datei.
  - Mehrere Aufrufe in derselben Sekunde → kollidieren nicht (z. B. via `_HHMMSS_NNN` als Fallback oder Test toleriert "ein Backup pro Sekunde").
  - Cleanup-Test: 10 Auto-Backups + 3 manuelle → nach Cleanup 7 Auto + 3 manuell.

## Offene Fragen

- **Alt-Backups (`app_YYYY-MM-DD.db` ohne Trigger-Suffix):** Einmalig umbenennen (auf `_auto`) oder im Cleanup-Glob mit-berücksichtigen? Vorschlag: Im Cleanup tolerieren (Glob `app_*.db` weiterhin matchen, aber `_manual`-Suffix ausschließen).
- **Mehrere manuelle Backups pro Sekunde:** Sollte praktisch nicht vorkommen, aber `FileExistsError` abfangen und Filename um Suffix `_2`, `_3` erweitern? Oder akzeptieren, dass max. 1 Backup/Sekunde geht?
- **Begrenzung manueller Backups:** Sollen manuelle Backups auch eine Obergrenze haben (z. B. max. 20)? Aktuell laut Story unbegrenzt → könnte langfristig Speicherplatz fressen.
- **Toast-Timing beim Direkt-Download via `<a href>`:** Browser zeigt den Download in der eigenen UI an. Ist der Toast überhaupt nötig? Alternativ: nur "Pfad kopiert"-Toast und Download-Feedback dem Browser überlassen.
