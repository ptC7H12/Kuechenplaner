# Story 30: Zutatenkategorien manuell verwalten

**Status:** Done
**Aufwand:** Mittel
**Machbarkeit:** Sehr gut
**Implementiert in:** `app/models.py:96-135` (Category-Tabelle + Ingredient.category_id), `app/schemas.py:43-90` (Category-/Ingredient-Schemas), `app/crud.py:202-302` (Category-CRUD, update_ingredient, get_or_create_ingredient), `alembic/versions/007_ingredient_categories.py` (Migration + Datenmigration), `app/routers/settings.py:393-470` (POST/DELETE categories, GET/PATCH ingredients), `app/services/calculation.py:110-150` (Gruppierung über category.name + Farben), `app/routers/recipes.py:302-356`, `app/routers/shopping_list.py:26-34`, `app/templates/settings/index.html` (Tags-Hinweis, Kategorien-Abschnitt, Zutaten-Tab), `app/templates/settings/_category_card.html`, `app/templates/settings/_ingredient_row.html`, `app/templates/settings/_ingredients_table.html`, `app/templates/shopping_list.html:95-105` (farbiger Gruppen-Header), `app/templates/recipes/detail.html`, `app/templates/recipes/edit.html`, `tests/test_settings_categories.py`

## Beschreibung

Als Küchenplaner möchte ich Zutaten einer eigenen Kategorie zuordnen und neue Kategorien anlegen oder löschen können — genau wie ich Tags für Rezepte verwalte —, damit die Einkaufsliste sinnvoll gruppiert wird und nicht von der automatischen Raten-Logik abhängt.

## Ist-Zustand

- `app/models.py:85` — `Ingredient.category` ist ein freies String-Feld (max. 100 Zeichen); kein Enum, keine eigene Tabelle.
- `app/routers/settings.py:317-412` — `_guess_ingredient_category()` belegt die Kategorie einmalig beim Excel-Import per Keyword-Matching; danach ist keine Änderung möglich.
- `app/crud.py:193-205` — `get_or_create_ingredient()` setzt die Kategorie nur beim **Anlegen**; kein `update_ingredient`-Pendant in `crud.py`.
- `app/schemas.py:47-51` — `IngredientUpdate` mit optionalem `category`-Feld existiert bereits, wird aber nirgends von einem Endpoint genutzt.
- `app/templates/shopping_list.html:98-129` — Einkaufsliste gruppiert dynamisch nach `category`; jede neue Kategorie taucht automatisch als Block auf.
- **Tags als Vorbild:** `app/models.py:140-151` — `Tag`-Tabelle (id, name, color, icon); `app/crud.py:266-307` — vollständige Tag-CRUD; `app/routers/settings.py:327-374` — POST `/settings/api/tags` + DELETE `/settings/api/tags/{id}`; `app/templates/settings/index.html:188-273` — Settings-Tab "Tags & Kategorien" mit Karten-Grid + Formular.
- Kein Router-Endpoint und keine UI zum Bearbeiten von Zutatenkategorien vorhanden.

## Akzeptanzkriterien

- [x] `Ingredient.category` wird durch eine FK-Beziehung zu einer neuen `categories`-Tabelle ersetzt (id, name, color); Alembic-Migration mit Datenmigration der vorhandenen String-Werte.
- [x] Im Settings-Tab "Tags & Kategorien" gibt es einen **Kategorien-Abschnitt** (analog zum Tags-Abschnitt), der alle vorhandenen Kategorien als Karten mit Name und Farbe anzeigt, inkl. Löschen-Button.
  - Der Kategorien-Abschnitt trägt den erklärenden Hinweis: *„Kategorien gruppieren Zutaten in der Einkaufsliste."*
  - Der Tags-Abschnitt erhält den erklärenden Hinweis: *„Tags helfen beim Filtern von Rezepten im Speiseplan."*
- [x] Neue Kategorien können per Formular angelegt werden (Name + Farbe, analog Tag-Formular); leere Namen werden abgelehnt (422).
- [x] Kategorien können gelöscht werden; Zutaten, die diese Kategorie haben, bekommen `category_id = NULL` (oder eine Default-Kategorie „Sonstiges").
- [x] In der Zutaten-Verwaltung (Einstellungen → Zutaten) ist jede Zutat mit ihrer aktuellen Kategorie aufgelistet; per Inline-Edit (`<select>` der vorhandenen Kategorien) kann die Zuweisung geändert werden.
- [x] Die Änderung wird sofort in der Einkaufsliste (Gruppierung) sichtbar.
- [x] Gleichzeitig kann die Einheit einer Zutat ebenfalls editiert werden (da `IngredientUpdate` beides abdeckt).
- [x] Pytest deckt ab: `update_ingredient` in `crud.py`; Endpoint PATCH `/settings/ingredients/{id}`; Kategorie-Änderung schlägt bei leerem Namen fehl; Kategorie-Anlegen und -Löschen.

## Technische Umsetzung (Vorschlag)

### Datenmodell

- **`app/models.py`** — neue `Category`-Tabelle analog zu `Tag`:
  ```
  id, name (unique, indexed), color (default "#6B7280"), created_at, updated_at
  ```
- **`Ingredient.category`** (String) → **`Ingredient.category_id`** (FK → `categories.id`, nullable).
- **Alembic-Migration** — neue Tabelle `categories` anlegen; vorhandene `category`-Strings in `categories`-Zeilen überführen; `category_id` setzen; Spalte `category` entfernen.

### Backend

- **`app/schemas.py`** — `CategoryBase`, `CategoryCreate`, `Category`-Schemas (analog `TagBase` / `TagCreate` / `Tag`); `IngredientUpdate.category_id` (Optional[int]) statt `category` (Optional[str]); `@field_validator` gegen leeren `name` in `CategoryCreate`.
- **`app/crud.py`** — `get_categories`, `create_category`, `delete_category`, `get_or_create_category` (analog Tag-CRUD, `crud.py:266-307`); `update_ingredient(db, ingredient_id, data: IngredientUpdate)` für category_id + unit.
- **`app/routers/settings.py`** — neue Endpoints analog Tag-Endpoints:
  - `POST /settings/api/categories` — Kategorie anlegen; gibt HTML-Karte zurück (`hx-swap="afterbegin"`).
  - `DELETE /settings/api/categories/{category_id}` — Kategorie löschen; gibt leeres `HTMLResponse` zurück.
  - `PATCH /settings/ingredients/{ingredient_id}` — Zutat aktualisieren (category_id + unit); gibt aktualisierte Tabellenzeile als HTML-Fragment zurück (`HX-Reswap: outerHTML`).
  - `GET /settings/ingredients` (oder als Tab im bestehenden Settings-Endpoint) — Zutaten-Tabelle mit Kategorie-Select rendern.

### Frontend

- **`app/templates/settings/index.html`**:
  - Im Tags-Abschnitt (ca. Zeile 188) Hinweistext ergänzen: *„Tags helfen beim Filtern von Rezepten im Speiseplan."*
  - Neuer **Kategorien-Abschnitt** direkt darunter (analog Zeilen 204-272): Karten-Grid mit Kategorie-Name + Farbe + Löschen-Button; Formular mit Name + Farb-Picker; Hinweistext: *„Kategorien gruppieren Zutaten in der Einkaufsliste."*
- **Zutaten-Tab** im Settings (neuer Reiter oder Unterbereich): Tabelle aller Zutaten mit Spalten Name / Einheit / Kategorie; Kategorie-Spalte als `<select>` der vorhandenen Kategorien (`hx-patch`, `hx-trigger="change"`); Suchfeld per `hx-get` + `keyup changed delay:300ms`.
- **`app/templates/shopping_list.html`** — Gruppierung von `category` (String) auf `ingredient.category.name` (Objekt-Attribut) umstellen; Gruppen-Header mit `background-color: {category.color}20` und `border-left: 4px solid {category.color}` einfärben (analog Tag-Badge-Stil).

### Tests

- `tests/test_crud.py` — `update_ingredient` mit gültigen Daten und `category_id=None`.
- `tests/test_settings.py` (neu oder vorhanden) — POST `/settings/api/categories` (anlegen), DELETE (löschen), PATCH `/settings/ingredients/{id}` mit gültigen Daten und mit leerem Kategorienamen (422).

## Entschiedene Fragen

- **Excel-Import:** `_guess_ingredient_category()` bleibt erhalten; beim Import wird `get_or_create_category(name)` aufgerufen, sodass erkannte Kategorien automatisch angelegt werden. Der User kann die Zuweisung danach manuell überschreiben.
- **Farbe:** Die Kategorie-Farbe wird in der Einkaufsliste als farbiger Gruppen-Header angezeigt (konsistent mit der Farbe in der Verwaltungsansicht).
