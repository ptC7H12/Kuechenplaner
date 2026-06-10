# Story 33: Allergene in den Einstellungen verwalten

**Status:** Done
**Aufwand:** Klein-Mittel
**Machbarkeit:** Sehr gut
**Implementiert in:** `app/crud.py:559-589` (`get_allergen_by_name`, `delete_allergen`), `app/routers/settings.py:419-457` (POST/DELETE `/api/allergens`), `app/templates/settings/_allergen_card.html` (neu), `app/templates/settings/index.html:336-393` (Allergene-Abschnitt), `tests/test_settings_allergens.py` (neu)

## Beschreibung

Als Küchenplaner möchte ich Allergene in den Einstellungen anlegen und löschen können — genauso wie ich Tags und Zutatenkategorien verwalte —, damit ich eine gepflegte Allergen-Liste habe, die ich Rezepten zuordnen kann.

## Ist-Zustand

- `app/models.py:191-201` — `Allergen`-Modell (name, icon) existiert bereits; `recipe_allergen_table` (`app/models.py:41-46`) als M:N-Verknüpfung zu Recipe.
- `app/schemas.py:134-149` — `AllergenBase` / `AllergenCreate` / `Allergen`-Schemas vorhanden.
- `app/crud.py:560-588` — `get_allergen`, `get_allergens`, `create_allergen`, `get_or_create_allergen`; es gibt **kein** `delete_allergen`.
- `app/routers/allergens.py:10-28` — nur JSON-API (GET-Liste, GET-Einzeln, POST); keine UI, keine DELETE-Route.
- `app/routers/settings.py:96-105` — `get_allergens(db)` wird bereits geladen und in den Settings-Context gegeben, aber **nicht** als verwaltbarer Abschnitt gerendert.
- **Vorbild Tags:** `app/templates/settings/index.html:194-280` (Karten-Grid + Formular); Endpoints `app/routers/settings.py:331-378` (POST/DELETE Tags).
- **Vorbild Kategorien:** `app/templates/settings/_category_card.html`; Endpoints `app/routers/settings.py:382-410`.

## Akzeptanzkriterien

- [x] Im Settings-Tab „Tags & Kategorien" gibt es einen **Allergene-Abschnitt** (analog Tags/Kategorien) mit Karten-Grid (Name + Icon) und Löschen-Button.
- [x] Neue Allergene können per Formular angelegt werden (Name + optionales Icon); leerer Name wird abgelehnt (422).
- [x] Allergene können gelöscht werden; bestehende Recipe-Verknüpfungen werden über die M:N-Tabelle sauber entfernt (kein Constraint-Fehler).
- [x] HTMX-Pattern wie bei Tags: `hx-post` → `hx-swap="afterbegin"`; `hx-delete` → `outerHTML swap:0.3s` mit `hx-confirm`.
- [x] Pytest deckt ab: `delete_allergen` in `crud.py`; POST-Endpoint (anlegen + leerer Name → 422) und DELETE-Endpoint (löschen entfernt M:N-Einträge).

## Technische Umsetzung (Vorschlag)

### Backend

- `app/crud.py` — `delete_allergen(db, allergen_id)` ergänzen (analog `delete_tag` `app/crud.py:361-367`); vor dem Löschen die `recipe_allergen_table`-Einträge des Allergens entfernen bzw. `db.delete(allergen)` mit korrekt konfigurierter Relation nutzen.
- `app/routers/settings.py` — neue Endpoints analog Tag-Endpoints:
  - `POST /settings/api/allergens` — Allergen anlegen (Validierung über `AllergenCreate`); gibt Karten-Fragment zurück (`hx-swap="afterbegin"`), Status 201.
  - `DELETE /settings/api/allergens/{allergen_id}` — Allergen löschen; gibt leeres `HTMLResponse(status_code=200)` zurück.

### Frontend

- `app/templates/settings/_allergen_card.html` (neu) — Karten-Fragment analog `_category_card.html` (Name + Icon + Löschen-Button mit `hx-delete`).
- `app/templates/settings/index.html` — neuer **Allergene-Abschnitt** direkt unter dem Kategorien-Abschnitt: Karten-Grid (`id="allergens-grid"`) + Formular (Name + optionales Icon) mit `hx-post="/settings/api/allergens"`, `hx-target="#allergens-grid"`, `hx-swap="afterbegin"`. Erklärender Hinweis: *„Allergene können Rezepten zugeordnet und in Listen/Exporten ausgegeben werden."*
- Keine Alembic-Migration nötig (Tabelle `allergens` existiert bereits).

### Tests

- `tests/test_settings_allergens.py` (neu) — POST `/settings/api/allergens` (anlegen, leerer Name → 422), DELETE `/settings/api/allergens/{id}` (löschen entfernt Recipe-Verknüpfung), `crud.delete_allergen`.
