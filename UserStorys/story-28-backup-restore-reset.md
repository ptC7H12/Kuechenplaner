# Story 28: Backup wiederherstellen & Datenbank zurücksetzen funktional machen

**Status:** Done
**Aufwand:** Mittel
**Machbarkeit:** Gut
**Implementiert in:** `app/database.py:134-322` (`_PROTECTED_TRIGGERS`, `_validate_backup_file`, `_alembic_known_revisions`, `restore_database`, `reset_database`), `app/routers/settings.py:84-185` (Restore/Reset-Endpoints + Flash-Cookie-Helper), `app/templates/settings/index.html:431-505` (Restore-/Reset-Karten), `app/templates/base.html:298-321` (Flash-Toast + HX-Trigger-Reader), `tests/test_backup_restore.py`, `tests/test_backup_reset.py`.
**Abhängigkeit:** [Story 27](story-27-backup-download-feedback.md) — gemeinsamer Backup-Pfad (`<DATA_DIR>/backups/`), `.db`-Format und `backup_database(trigger=...)`-Helper.

**Entscheidungen (aus offenen Fragen geklärt):**

- Scope Phase 1: **nur Upload** (kein Dropdown der vorhandenen Backups — wäre Folge-Story).
- Concurrency: Reliance auf SQLite-WAL + `engine.dispose()`, kein expliziter App-Lock.
- Cookie nach Restore: `current_camp_id` wird beim Restore-Endpoint gelöscht; nach `HX-Refresh` landet der User wieder auf `/select-camp`.
- Toast-Mechanik nach `HX-Refresh`: **Flash-Cookie** (`flash_toast`, JSON-kodiert) wird im Endpoint gesetzt, in `base.html` per `x-init` ausgelesen, sofort gelöscht und über `FreizeitApp.showToast()` angezeigt.
- UI-Hinweistext: Karten erhalten zusätzlich den kleinen Hinweis *"Falls Probleme auftreten, App neu starten."* (deckt pywebview-Edge-Cases).

## Beschreibung

Im Backup-Tab der Einstellungen existieren UI-Karten für "Backup wiederherstellen" und "Datenbank zurücksetzen", die aktuell reine HTML-Mockups ohne Backend-Anbindung sind. Als Küchenplaner möchte ich

- ein vorhandenes `.db`-Backup hochladen und wiederherstellen können (mit Sicherheits-Backup der aktuellen DB vor dem Überschreiben),
- die Datenbank komplett zurücksetzen können (mit doppelter Bestätigung und Sicherheits-Backup),

damit ich nach Datenverlust oder beim Wechsel zwischen Saisons / Lagern flexibel arbeiten kann.

## Ist-Zustand

- `app/templates/settings/index.html:431-458` — Restore-Karte: File-Input ohne `name`, kein `<form>`-Tag, Button ohne Handler. Input-Filter ist `accept=".zip"` — passt **nicht** zum tatsächlichen Backup-Format `.db` (siehe `app/database.py:144`). Vermutlich Reststand eines ursprünglich geplanten ZIP-Backup-Workflows, der nie umgesetzt wurde.
- `app/templates/settings/index.html:460-493` — Reset-Karte: Text-Input für Bestätigungswort "LÖSCHEN" ohne `x-model`, Button hartkodiert `disabled` und ohne Handler.
- `app/routers/settings.py` — keine Restore- oder Reset-Endpoints. Grep nach `restore`/`reset_database`/`drop_all` im `app/`-Tree liefert keine Treffer.
- `FreizeitApp.showToast(message, type)` ist in `app/templates/base.html:219` global verfügbar; Migrations-Helper `run_migrations()` in `app/database.py:92`.

## Akzeptanzkriterien

- [x] Restore-Input akzeptiert nur `.db` (nicht `.zip` wie aktuell).
- [x] Restore validiert Datei: SQLite-Header (`b"SQLite format 3\x00"`) + Tabelle `alembic_version` mit Revision vorhanden. Ungültige Datei → Toast `error`, kein Datenverlust.
- [x] Vor jedem Restore wird ein Sicherheits-Backup `app_{ts}_pre-restore.db` angelegt.
- [x] Nach erfolgreichem Restore läuft `alembic upgrade head` automatisch; ältere Backups werden auf das aktuelle Schema migriert.
- [x] Backup mit Revision **neuer** als der laufende App-`head` → Restore wird abgelehnt (Toast `error`, kein Datenverlust).
- [x] Nach Restore: `engine.dispose()` + `HX-Refresh: true` + Toast `'Backup wiederhergestellt'` (`success`).
- [x] Reset-Button ist disabled, bis Nutzer "LÖSCHEN" exakt eingegeben hat (Alpine `x-model` + `:disabled`).
- [x] Reset legt vorher Sicherheits-Backup `app_{ts}_pre-reset.db` an, löscht `app.db`, läuft Migrations, refresht via `HX-Refresh`.
- [x] Beide Aktionen zeigen einen `hx-confirm`-Dialog als zweite Absicherung (zusätzlich zum Warning-Banner).
- [x] Pytest deckt Happy-Path und Validierungs-Fehler für beide Endpoints ab.

## Technische Umsetzung (Vorschlag)

### Backend

`app/database.py` — neue Helper:

- `_validate_backup_file(path: Path) -> None` — prüft SQLite-Header, `sqlite3.connect`, Existenz `alembic_version` mit Revision; wirft `ValueError` bei Fehler.
- `restore_database(uploaded: Path) -> None` — `backup_database(trigger="pre-restore")`, dann `engine.dispose()`, `os.replace(uploaded, DATA_DIR / "app.db")`, `run_migrations()`.
- `reset_database() -> None` — `backup_database(trigger="pre-reset")`, `engine.dispose()`, `(DATA_DIR / "app.db").unlink(missing_ok=True)`, `run_migrations()`.

`app/routers/settings.py` — zwei neue Endpoints:

```python
@router.post("/database/restore")
async def restore_database_endpoint(backup_file: UploadFile = File(...)):
    tmp = save_upload_to_temp(backup_file)  # temp file in DATA_DIR
    try:
        _validate_backup_file(tmp)
        restore_database(tmp)
    except ValueError as e:
        return Response(status_code=400, headers={"HX-Trigger": json.dumps({"toast": {"message": str(e), "type": "error"}})})
    return Response(headers={"HX-Refresh": "true"})

@router.post("/database/reset")
async def reset_database_endpoint():
    reset_database()
    return Response(headers={"HX-Refresh": "true"})
```

Toast nach Refresh: Flash-Cookie setzen (z. B. `flash_toast={"message":"…","type":"success"}`), in `base.html` per `x-init` auslesen + Cookie löschen + `showToast()` aufrufen.

### Frontend

`app/templates/settings/index.html:431-458` — Restore-Karte umbauen:

```html
<form hx-post="/settings/database/restore"
      hx-encoding="multipart/form-data"
      hx-confirm="Wirklich wiederherstellen? Aktuelle Daten werden überschrieben (Sicherheits-Backup wird angelegt).">
    <input type="file" name="backup_file" accept=".db" required class="form-input">
    <button type="submit" class="btn btn-primary btn-md">Backup wiederherstellen</button>
</form>
```

`app/templates/settings/index.html:460-493` — Reset-Karte umbauen:

```html
<div x-data="{ confirm: '' }" class="space-y-4">
    <input x-model="confirm" type="text" class="form-input" placeholder="LÖSCHEN">
    <button :disabled="confirm !== 'LÖSCHEN'"
            hx-post="/settings/database/reset"
            hx-confirm="LETZTE WARNUNG: Alle Daten gehen verloren."
            class="btn btn-danger btn-md">
        Alle Daten löschen
    </button>
</div>
```

### Tests

- `tests/test_backup_restore.py`:
  - Valide `.db` mit `alembic_version` → 200, neuer DB-Inhalt sichtbar, pre-restore-Backup existiert.
  - Datei ohne SQLite-Header → 400.
  - SQLite-Header aber ohne `alembic_version` → 400.
  - Revision neuer als `head` → 400.
- `tests/test_backup_reset.py`:
  - POST `/settings/database/reset` → 200, DB ist leer (nur Schema), pre-reset-Backup existiert.

