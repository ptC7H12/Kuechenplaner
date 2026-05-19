# TECHNICAL README - Kuechenplaner
> **Quick Reference für AI-Assistenten** | Zuletzt aktualisiert: 2026-05-15

## 🎯 Projekt-Übersicht
**Typ:** Desktop-App für Freizeit-/Camp-Rezeptverwaltung
**Stack:** FastAPI + HTMX + Tailwind CSS + pywebview
**DB:** SQLite mit SQLAlchemy ORM
**Port:** 12000
**Entry Point:** `app/main.py`

## 📁 Projektstruktur
```
Kuechenplaner/
├── app/
│   ├── main.py              # FastAPI-App, Server-Start, Routen
│   ├── models.py            # SQLAlchemy-Modelle (siehe Datenmodell)
│   ├── schemas.py           # Pydantic-Schemas für API
│   ├── crud.py              # Datenbank-CRUD-Operationen
│   ├── database.py          # DB-Setup, Session, Migrations, Backup
│   ├── seeders.py           # Default-Daten (Tags, Allergene, Zutaten)
│   ├── constants.py         # Modul-übergreifende Konstanten
│   ├── dependencies.py      # FastAPI-Dependencies (get_current_camp, etc.)
│   ├── routers/             # API-Endpunkte (siehe API-Referenz)
│   │   ├── camps.py         # /api/camps/*
│   │   ├── recipes.py       # /recipes/*
│   │   ├── allergens.py     # /api/allergens/*
│   │   ├── meal_planning.py # /meal-planning/*
│   │   ├── shopping_list.py # /shopping-list/*
│   │   ├── export.py        # /export/* (PDF, Excel)
│   │   ├── leftovers.py     # /leftovers/* (Reste-Tracker, Statistik)
│   │   └── settings.py      # /settings/*
│   ├── services/
│   │   ├── calculation.py   # Skalierung, Einkaufslisten-Berechnung
│   │   ├── leftover_statistics.py # Aggregat-Statistik für Reste pro Rezept
│   │   └── unit_converter.py # g↔kg, ml↔L Konvertierung
│   ├── templates/           # Jinja2-Templates (HTMX)
│   └── static/
│       ├── css/             # custom.css
│       ├── js/
│       │   ├── layout.js    # Sidebar-Toggle (auf jeder Seite geladen)
│       │   └── recipe-form.js # Alpine-Komponenten für Recipe Create/Edit
│       └── (Icons, Favicon)
├── alembic/                 # DB-Migrations (siehe „Datenbank-Migrationen")
│   ├── env.py
│   └── versions/
│       ├── 001_initial_schema.py
│       ├── 002_meal_plan_recipe_nullable.py
│       ├── 003_shopping_notes.py            # Ingredient.note + shopping_list_notes
│       ├── 004_meal_plan_custom_servings.py # MealPlan.custom_servings
│       ├── 005_meal_plan_sub_category.py    # MealPlan.sub_category
│       └── 006_leftovers.py                 # leftovers Tabelle
├── tests/                   # pytest-Suite (siehe „Tests & Tooling")
│   ├── conftest.py          # In-Memory-SQLite-Fixture, TestClient
│   ├── test_health.py
│   ├── test_crud_camp.py
│   ├── test_schemas.py
│   ├── test_unit_converter.py
│   ├── test_shopping_notes.py           # Story 2
│   ├── test_recipe_preview.py           # Story 4
│   ├── test_meal_plan_custom_servings.py # Story 1
│   ├── test_export_daily_lists.py       # Story 3
│   └── test_leftovers.py                # Story 5
├── pyproject.toml           # ruff, mypy, pytest config
├── requirements.txt         # Runtime-Dependencies (gepinnt)
├── requirements-build.txt   # Build-Dependencies (Nuitka, Pillow — gepinnt)
├── requirements-dev.txt     # Dev-Dependencies (pytest, ruff, mypy)
├── build.py                 # Nuitka-Build für Standalone-Exe
├── build_windows_standalone.py  # Embedded-Python ZIP-Build
└── build_logging.py         # Tee-Logger: spiegelt print() in logs/build_*.log
```

## 🗄️ Datenmodell (models.py)

### Kern-Entitäten
| Tabelle | Beschreibung | Wichtige Felder |
|---------|-------------|-----------------|
| **Camp** | Freizeit/Veranstaltung | `name`, `start_date`, `end_date`, `participant_count` |
| **Recipe** | Global wiederverwendbare Rezepte | `name`, `base_servings`, `version_number` |
| **Ingredient** | Zutat-Stammdaten | `name`, `unit`, `category` (z.B. "Gemüse"), `note` (global, optional) |
| **RecipeIngredient** | Zutat in Rezept (M:N) | `recipe_id`, `ingredient_id`, `quantity`, `unit` |
| **MealPlan** | Rezept zu Mahlzeit zugeordnet | `camp_id`, `recipe_id`, `meal_date`, `meal_type`, `position`, `custom_servings` (optional), `sub_category` (optional, nur bei DINNER üblich) |
| **Tag** | Kategorien (M:N zu Recipe) | `name`, `color`, `icon` (z.B. "Frühstück" 🌅) |
| **Allergen** | Allergene (M:N zu Recipe) | `name`, `icon` (z.B. "Gluten" 🌾) |
| **RecipeVersion** | Rezept-Snapshots | `recipe_id`, `version_number`, `ingredients_snapshot` (JSON) |
| **ShoppingListNote** | Camp-spezifische Notiz pro Zutat | `camp_id`, `ingredient_id`, `note` (UNIQUE pro Paar) |
| **Leftover** | Erfasste Reste nach einer Mahlzeit | `camp_id`, `meal_plan_id`, `recipe_id`, `ingredient_id`, `tracking_type` (`per_recipe`/`per_ingredient`), `percentage_left` (0-100), `description` |
| **AppSettings** | Key-Value-Store | `key`, `value` (JSON) |

### MealType Enum
```python
class MealType(enum.Enum):
    BREAKFAST = "BREAKFAST"
    LUNCH = "LUNCH"
    DINNER = "DINNER"
```

### Sub-Kategorien (Mahlzeiten-Gänge)
Frei wählbar pro `MealPlan` (typischerweise nur bei DINNER gesetzt) — Validierung in `schemas.py` gegen `constants.MEAL_SUB_CATEGORIES`:
```python
MEAL_SUB_CATEGORIES = ["Vorspeise", "Hauptgang", "Beilage", "Salat", "Nachtisch"]
```

### Wichtige Constraints
- **Camp:** `start_date <= end_date`, `participant_count > 0`
- **MealPlan:** UNIQUE(`camp_id`, `meal_date`, `meal_type`, `position`), `custom_servings > 0` (Pydantic)
- **RecipeVersion:** UNIQUE(`recipe_id`, `version_number`)
- **ShoppingListNote:** UNIQUE(`camp_id`, `ingredient_id`), beide FKs `ON DELETE CASCADE`
- **Leftover:** `percentage_left` ∈ [0, 100] (Pydantic); `tracking_type` muss `per_recipe` oder `per_ingredient` sein; `ingredient_id` Pflicht bei `per_ingredient`

### Beziehungen
```
Camp 1───N MealPlan N───1 Recipe
  │                       ├─N RecipeIngredient N─1 Ingredient
  │                       ├─N Tag (M:N)
  │                       ├─N Allergen (M:N)
  │                       └─N RecipeVersion
  ├───N ShoppingListNote N───1 Ingredient
  └───N Leftover (cascade delete-orphan)
              ├─0..1 MealPlan
              ├─0..1 Recipe
              └─0..1 Ingredient
```

## 🔌 API-Endpunkte (Auswahl)

### Camps (`/api/camps/`)
- `GET /api/camps/` - Alle Freizeiten
- `POST /api/camps/` - Neue Freizeit
- `PUT /api/camps/{id}` - Freizeit bearbeiten
- `DELETE /api/camps/{id}` - Freizeit löschen (CASCADE: löscht alle MealPlans!)
- `POST /api/camps/{id}/select` - Freizeit auswählen (setzt Cookie)

### Recipes (`/recipes/`)
- `GET /recipes/` - Rezept-Liste (HTML, mit Statistiken, Sortierung, Filter)
- `GET /recipes/create` - Rezept-Formular (Material Design, Autocomplete)
- `POST /recipes/` - Neues Rezept erstellen (JSON: ingredients, tag_ids)
- `GET /recipes/{id}` - Rezept-Detail (HTML)
- `GET /recipes/{id}/preview?servings=N` - **Story 4:** HTML-Fragment für Vorschau-Modal aus der Wochenübersicht (optional skaliert)
- `GET /recipes/{id}/edit` - Rezept bearbeiten (vorausgefüllt)
- `POST /recipes/{id}` - Rezept aktualisieren (**erstellt neue Version**)
- `DELETE /recipes/{id}` - Rezept löschen
- `GET /recipes/api/search` - Suche & Filter (`?search=...&tag_ids=...`)
- `GET /recipes/api/ingredients/search?q=` - Fuzzy-Search für Autocomplete
- `POST /recipes/api/ingredients/quick-create` - Zutat während Rezept-Erstellung

### Meal Planning (`/meal-planning/`)
- `GET /meal-planning/` - Kalender-Ansicht (mit `meal_sub_categories` im Context)
- `POST /meal-planning/api/meal-plans` - Mahlzeit anlegen (JSON; akzeptiert `custom_servings`, `sub_category`)
- `PUT /meal-planning/api/meal-plans/{id}` - Mahlzeit aktualisieren (Position, Notes, `custom_servings`, `sub_category`)
- `DELETE /meal-planning/api/meal-plans/{id}` - Mahlzeit entfernen
- `POST /meal-planning/api/meal-plans/bulk` - Mehrere Mahlzeiten in einem Request
- `POST /meal-planning/api/meal-plans/{id}/copy` - Mahlzeit kopieren

### Shopping List (`/shopping-list/`)
- `GET /shopping-list/` - Einkaufsliste (HTML)
- `GET /shopping-list/api/shopping-list?camp_id=` - Berechnete Liste (JSON)
- `GET /shopping-list/api/shopping-list/summary?camp_id=` - Summary mit Statistiken
- `PUT /shopping-list/api/shopping-list/notes/{ingredient_id}` - **Story 2:** Camp-spezifische Bemerkung setzen/aktualisieren (leerer String = löschen). Body: `{note: str}`. Nutzt aktuelles Camp aus Cookie.
- `PUT /shopping-list/api/ingredients/{ingredient_id}/note` - **Story 2:** Globale Notiz auf einer Zutat (gilt camp-übergreifend)

### Export (`/export/`)
- `GET /export/shopping-list/pdf/{camp_id}` - Einkaufsliste als PDF (kompaktes Layout mit Bemerkungs-Spalte ab Story 2)
- `GET /export/shopping-list/excel/{camp_id}` - Einkaufsliste als Excel
- `GET /export/meal-plan/pdf/{camp_id}` - Speiseplan-Übersichts-PDF (Landscape-Tabelle, 10 Tage/Seite)
- `GET /export/recipe-book/pdf/{camp_id}` - Rezeptbuch-PDF (skaliert mit `max(custom_servings, camp.participant_count)` pro Rezept)
- `GET /export/daily-lists/pdf/{camp_id}` - **Story 3:** Tageslisten-PDF: ein Tag pro Seite, gruppiert nach `meal_type` + `sub_category`, 3-Spalten-Layout (Menge | Zutat | Zubereitung)
- `GET /export/recipes/pdf` - Komplette Rezeptsammlung als PDF mit Inhaltsverzeichnis

### Leftovers (`/leftovers/`) — Story 5
- `GET /leftovers/` - Übersicht aller Reste fürs aktuelle Camp (HTML)
- `GET /leftovers/new?meal_plan_id=` - Modal-Fragment zur Erfassung (über `FreizeitApp.openModal()`)
- `GET /leftovers/statistics` - Aggregat-Statistik pro Rezept + Skalierungsvorschlag fürs aktuelle Camp
- `POST /leftovers/api/leftovers` - Eintrag anlegen (JSON: `LeftoverCreate`)
- `GET /leftovers/api/leftovers/camp/{camp_id}` - JSON-Liste fürs Camp
- `GET /leftovers/api/leftovers/statistics/{recipe_id}` - Aggregat für ein einzelnes Rezept
- `DELETE /leftovers/api/leftovers/{id}` - Eintrag löschen

## ⚙️ Wichtige Services

### `services/calculation.py`
**Funktionen:**
- `scale_recipe(recipe, target_servings)` → skaliert die Zutaten eines Rezepts auf eine Zielportionszahl
- `calculate_shopping_list(db, camp_id)` → Aggregierte Einkaufsliste
  - Lädt alle MealPlans für Camp
  - **Skaliert pro Eintrag mit `meal_plan.custom_servings or camp.participant_count`** (Story 1)
  - Aggregiert Zutaten nach `(ingredient_id, unit)`
  - Konvertiert Einheiten (g→kg, ml→L)
  - Gruppiert nach `category`
  - Reichert jedes Item mit `note` (camp-spezifisch) und `global_note` (Ingredient.note) an (Story 2)
- `get_camp_statistics(db, camp_id)` → Dashboard-Statistiken

### `services/leftover_statistics.py` — Story 5
- `get_recipe_statistics(db, recipe_id, current_camp_id=None)` → Aggregat über alle Camps:
  - `avg_percentage_left` (Mittelwert über alle Einträge mit `percentage_left`)
  - `camps_with_leftovers` (Anzahl unterschiedlicher Camps mit >0% Rest)
  - **Skalierungsvorschlag:** wenn `avg_percentage_left > 10 %` und `current_camp_id` gesetzt, wird `suggested_servings = round(participant_count * (1 - avg/100))` zurückgegeben.

### `services/unit_converter.py`
**Konvertierungen:**
- `convert_unit(quantity, from_unit, to_unit)`
  - g ↔ kg (1000:1)
  - ml ↔ L (1000:1)
  - TL ↔ EL (3:1)
- **Best-Unit-Auswahl:** `>= 1000g` → `kg`, `>= 1000ml` → `L`

### `crud.py` - Wichtige Funktionen
- `search_ingredients_fuzzy(db, query, limit=10)` - Fuzzy-Matching für Zutaten
  - Verwendet `thefuzz.fuzz.partial_ratio()`
  - Scores: Exact=100, Starts-with=95, Contains=85, Fuzzy=0-100
  - Sortiert nach Score + Usage-Count
- `upsert_shopping_list_note(db, camp_id, ingredient_id, note)` — Story 2: leerer/whitespace-only Wert löscht die Camp-Notiz
- `update_ingredient_note(db, ingredient_id, note)` — Story 2: globale Notiz pro Zutat
- `get_shopping_list_notes_for_camp(db, camp_id) -> dict[int, str]` — Bulk-Lookup für die Einkaufslisten-Berechnung
- `create_leftover` / `get_leftovers_for_camp` / `get_leftovers_for_recipe` / `delete_leftover` — Story 5

## 🎨 Frontend-Architektur

### Technologien
- **Templates:** Jinja2 (`app/templates/`)
- **Interaktivität:** HTMX (partielle Updates ohne JS)
- **Styling:** Tailwind CSS
- **Icons:** Emoji + Heroicons

### Template-Struktur
```
templates/
├── base.html                # Layout, Navigation, lädt static/js/layout.js, globales Modal (#global-modal)
├── dashboard.html           # Startseite mit Statistiken
├── camp_select.html         # Freizeit-Auswahl
├── shopping_list.html       # Einkaufsliste (Note-Inputs pro Item, Story 2)
├── recipes/
│   ├── list.html           # Rezept-Liste (Statistiken, Sortierung, Livesearch)
│   ├── _form.html          # Gemeinsames Form-Markup (Create + Edit)
│   ├── create.html         # Wrapper: setzt RECIPE_FORM_CONFIG, includes _form.html
│   ├── edit.html           # Wrapper: setzt RECIPE_FORM_CONFIG mit initialData
│   ├── detail.html         # Rezept-Detailansicht
│   ├── preview_modal.html  # Story 4: HTML-Fragment, geladen ins #modal-content
│   └── partials/           # HTMX-Fragmente
├── meal_planning/
│   └── index.html          # Kalender-Grid (SortableJS Drag & Drop, custom_servings-Badge,
│                           #   sub_category-Button, „Reste erfassen"-Button)
├── leftovers/              # Story 5
│   ├── index.html          # Camp-Übersicht aller erfassten Reste
│   ├── new_modal.html      # Erfassungs-Modal (Alpine.js: tracking_type/Prozent/Beschreibung)
│   └── statistics.html     # Aggregat pro Rezept + Skalierungsvorschlag
└── components/
    ├── camp_stats.html, edit_camp_modal.html, ...
    └── forms.html          # Macros: text_input, number_input, textarea, select_field, date_input
```

### Alpine.js Components (in `app/static/js/recipe-form.js`)
- `recipeForm()` - Rezept-Formular; modusabhängig über `window.RECIPE_FORM_CONFIG`
- `ingredientAutocomplete()` - Fuzzy-Search für Zutaten (300ms Debounce)
- `newIngredientForm()` - Quick-Create-Modal für neue Zutaten
- `recipeList()` - Filter, Sortierung, Livesearch (in `recipes/list.html` inline, da seiten-spezifisch)

### Globale Helfer (`window.FreizeitApp`, definiert in `base.html`)
- `showToast(message, type)` — Toast-Notification (`success`/`error`/`warning`/`info`)
- `openModal(url)` — lädt eine URL per HTMX in `#modal-content` und dispatcht `open-modal`
- `closeModal()` — dispatcht `close-modal`
- `saveShoppingListNote(inputEl)` — Story 2: liest `data-ingredient-id` & `value`, PUTs `{note}` als JSON

### Globales Modal-Pattern
`base.html` enthält ein einziges `#global-modal` (Alpine `x-data`, reagiert auf `open-modal`/`close-modal`). Jede Seite, die ein Modal öffnen will, ruft `FreizeitApp.openModal('/fragment-url')` auf — der Endpoint muss ein HTML-Fragment liefern (kein vollständiges Template-Extends). Schließen via `$dispatch('close-modal')` innerhalb des Fragments.

Aktuelle Modal-Endpoints:
- `GET /recipes/{id}/preview?servings=N` → `recipes/preview_modal.html` (Story 4)
- `GET /leftovers/new?meal_plan_id=N` → `leftovers/new_modal.html` (Story 5)

### Recipe-Form: Create vs. Edit
Beide Templates teilen `recipes/_form.html` und `app/static/js/recipe-form.js`. Den Unterschied steuert ein Config-Block im jeweiligen Template:

```html
<script>
  window.RECIPE_FORM_CONFIG = {
    mode: 'create' | 'edit',
    submitUrl: '/recipes/' | '/recipes/<id>',
    submitMethod: 'POST' | 'PUT',
    redirectUrl: '/recipes/' | '/recipes/<id>',
    draftKey: 'recipe_draft' | null,   // null = kein LocalStorage-Draft (edit)
    initialData: null | { ...recipe }  // vorbefüllte Form-Daten (edit)
  };
</script>
<script src="/static/js/recipe-form.js"></script>
```

Bei Form-Erweiterungen (neue Felder etc.) muss **nur** noch `_form.html` und `recipe-form.js` angefasst werden.

### Form-Macros (`components/forms.html`)
Wiederverwendbare Form-Strukturen für statisches Markup ohne Alpine-Bindings:

```jinja
{% from "components/forms.html" import text_input, number_input, textarea, select_field, date_input %}

{{ text_input(name="title", label="Titel", required=true, help_text="Aussagekräftiger Name") }}
{{ number_input(name="count", label="Anzahl", min=1, required=true) }}
{{ select_field(name="category", label="Kategorie", options=[("a","A"),("b","B")]) }}
```

Macros nutzen die Design-System-Klassen (`.form-label`, `.form-input` etc.) und setzen `required`/`aria-hidden` korrekt.

### HTMX-Muster
```html
<!-- Beispiel: Rezept-Suche -->
<input hx-get="/recipes/search"
       hx-trigger="keyup changed delay:300ms"
       hx-target="#recipe-list">
```

### Design System (Material Design 3)
**🎨 Buttons:** `.btn-primary` (indigo), `.btn-secondary` (gray), `.btn-success` (green), `.btn-danger` (red), `.btn-accent` (teal)
**📝 Forms:** `.form-label`, `.form-input`, `.form-select`, `.form-textarea`, `.form-checkbox`, `.form-input-color`
**🃏 Cards:** `.card` (rounded-2xl), `.card-hover`
**🚀 FABs:** Extended FABs mit `bg-indigo-600` (primär), `bg-teal-600` (sekundär)
**🎨 Farben:** Indigo (primär), Teal (sekundär), Green (success), Red (danger)
**📦 Shadows:** `shadow-md` → `hover:shadow-lg` → `active:shadow-xl` → `shadow-2xl` (FABs)
**➡️ Details:** Siehe `docs/DESIGN_SYSTEM.md`

## 🔑 Wichtige Konzepte

### 1. Camp-Auswahl-Mechanismus
- **Cookie:** `current_camp_id` speichert aktuelles Camp
- **Dependency:** `get_current_camp(request)` in `dependencies.py`
- **Persistenz:** AppSettings `last_selected_camp_id`

### 2. Rezept-Skalierung
```python
# Standard: Camp-Teilnehmerzahl
effective_servings = meal_plan.custom_servings or camp.participant_count
scaling_factor = effective_servings / recipe.base_servings
scaled_quantity = ingredient.quantity * scaling_factor
```
- `MealPlan.custom_servings` (Story 1) überschreibt `camp.participant_count` pro Eintrag — wichtig für Frühstück mit weniger Personen.
- Greift überall: Einkaufsliste, Tageslisten-PDF, Rezept-Preview-Modal.
- Rezeptbuch-PDF wählt pro Rezept das **Maximum** aller `effective_servings`-Werte, damit eine gedruckte Variante alle Mahlzeiten abdeckt.

### 3. Rezept-Versionierung
- **Bei jedem Update:** Neues `RecipeVersion`-Objekt wird erstellt
- **Snapshot:** Zutaten/Tags/Allergene als JSON gespeichert
- **MealPlans:** Referenzieren immer aktuelle Recipe-Version (kein Snapshot!)

### 4. Position-System
- Mehrere Rezepte pro Mahlzeit möglich
- `position` = 0, 1, 2, ... (Sortierreihenfolge)
- Unique-Constraint verhindert Duplikate

## 🚀 Entwicklung

### Setup
```bash
# Runtime-Dependencies
pip install -r requirements.txt

# Optional: Dev-Tools (pytest, ruff, mypy)
pip install -r requirements-dev.txt

# Dev-Server starten (Port 12000)
DEVELOPMENT=1 python -m app.main
# Beim Start: Backup -> Migrations -> Default-Daten-Seeding
```

### Build (Standalone Windows)
```bash
python build_windows_standalone.py
# Schreibt zusätzlich nach logs/build_standalone_<timestamp>.log
```

### Tests & Lint
```bash
python -m pytest tests/ -q       # 51 Tests, läuft in <5 s
python -m ruff check app tests   # Lint
python -m ruff format app tests  # Auto-Format
python -m mypy app               # Type-Check (lockerer Modus)
```

### Wichtige Befehle
```bash
# DB neu erstellen (Achtung: Datenverlust!)
rm data/app.db          # Dev-DB-Datei löschen
python -m app.main      # Neu erstellen bei Startup (via Alembic)

# Excel-Import (siehe excel_import.py)
python excel_import.py recipes.xlsx
```

## 🗃️ Datenbank-Migrationen (Alembic)

### Wo liegt die DB?
- **Dev:** `data/app.db` (relativ zum Repo-Root)
- **Prod/Nuitka-Build:**
  - Windows: `%APPDATA%/KuechenApp/app.db`
  - Linux: `$XDG_DATA_HOME/KuechenApp/app.db` bzw. `~/.local/share/KuechenApp/app.db`
- **Backups:** `<DATA_DIR>/backups/app_YYYY-MM-DD.db` (täglich rotierend, max. 7)

### Wie wird das Schema beim App-Start aufgebaut?
`app.database.run_migrations()` wird in [main.py](app/main.py) im Lifespan-Startup aufgerufen. Es unterscheidet drei Fälle:

1. **Frische DB (keine Tabellen):** `alembic upgrade head` baut das vollständige Schema aus den Migrationen auf.
2. **Legacy-DB (Tabellen vorhanden, `alembic_version` fehlt):** Die DB wurde von einer Vorgänger-Version mit `Base.metadata.create_all()` erzeugt. Sie wird auf Revision `001` **gestempelt** (`alembic stamp 001`) und anschließend per `upgrade head` zum aktuellen Stand gezogen.
3. **Getrackte DB (`alembic_version` vorhanden):** Normales `upgrade head`.

`Base.metadata.create_all()` wird **nicht mehr** beim App-Start aufgerufen — Alembic ist die alleinige Quelle der Wahrheit für das Schema.

### Workflow: Schema-Änderung vornehmen
**Regel:** Jede Änderung an [app/models.py](app/models.py) braucht eine neue Alembic-Migration. `models.py` allein ändert die User-DB nicht.

```bash
# 1. models.py anpassen (Spalte hinzufügen/entfernen, Index, Constraint, ...)

# 2. Migration generieren (autogenerate vergleicht models.py mit DB)
alembic revision --autogenerate -m "kurze beschreibung"

# 3. Generiertes Skript in alembic/versions/ prüfen!
#    - Autogenerate erkennt nicht alles (z.B. CheckConstraint-Texte, ENUMs)
#    - Bei SQLite-Spaltenänderungen: batch_alter_table oder Tabellen-Rebuild nötig
#      (siehe alembic/versions/002_meal_plan_recipe_nullable.py als Vorlage)

# 4. Migration lokal testen
python -m app.main      # läuft upgrade head beim Start
# oder direkt:
alembic upgrade head
alembic downgrade -1    # Rollback prüfen
alembic upgrade head    # Wieder hoch

# 5. Migration committen ZUSAMMEN mit der models.py-Änderung
```

### SQLite-spezifische Fallen
- SQLite unterstützt kein `ALTER COLUMN`. Für Nullable-/Typ-/FK-Änderungen muss die Tabelle neu aufgebaut werden (`op.create_table` → `INSERT SELECT` → `op.drop_table` → `op.rename_table`). Vorlage: [002_meal_plan_recipe_nullable.py](alembic/versions/002_meal_plan_recipe_nullable.py).
- FKs werden ohne expliziten Namen erzeugt — `batch_alter_table.drop_constraint(name)` funktioniert dann nicht. Lieber Tabellen-Rebuild.
- `ondelete="CASCADE/SET NULL"` braucht in SQLite zur Laufzeit `PRAGMA foreign_keys=ON` (siehe [database.py](app/database.py)).

### Migrations-Historie
| Revision | Beschreibung |
|---|---|
| `001` | Initial-Schema (alle Tabellen, recipe_id NOT NULL) |
| `002` | meal_plans.recipe_id nullable + ON DELETE SET NULL |
| `003` | Story 2: `ingredients.note` (global) + neue Tabelle `shopping_list_notes` (camp-spezifisch) |
| `004` | Story 1: `meal_plans.custom_servings` (Integer, nullable) |
| `005` | Story 3: `meal_plans.sub_category` (String, nullable) |
| `006` | Story 5: neue Tabelle `leftovers` (camp_id CASCADE, recipe_id/meal_plan_id/ingredient_id SET NULL) |

## 🧪 Tests & Tooling

### Test-Suite
- **Framework:** `pytest` (siehe `requirements-dev.txt`)
- **Standort:** `tests/` (Top-Level, neben `app/`)
- **Konfiguration:** `[tool.pytest.ini_options]` in `pyproject.toml`
- **Isolation:** Jeder Test bekommt eine frische **In-Memory-SQLite** (Fixture `test_engine`/`db_session` in [tests/conftest.py](tests/conftest.py)); die echte `data/app.db` wird nie angefasst.
- **Lifespan-Bypass:** Die `_disable_lifespan_side_effects`-Autouse-Fixture monkey-patcht `backup_database`, `run_migrations`, `init_default_data` zu No-Ops, damit Tests keine Backups oder Seeders auf der echten DB triggern.

```bash
python -m pytest tests/ -q              # alle Tests
python -m pytest tests/test_crud_camp.py -v  # einzelne Datei
```

**Aktueller Stand:** 51 Tests in 9 Dateien:
- Basics: `test_health.py`, `test_unit_converter.py`, `test_crud_camp.py`, `test_schemas.py`
- Story 2: `test_shopping_notes.py`
- Story 4: `test_recipe_preview.py`
- Story 1: `test_meal_plan_custom_servings.py`
- Story 3: `test_export_daily_lists.py`
- Story 5: `test_leftovers.py`

### Lint & Format (Ruff)
- **Konfiguration:** `[tool.ruff]` in `pyproject.toml`
- **Aktive Regeln:** `E,W,F,I,UP,B,SIM` (pycodestyle, pyflakes, isort, pyupgrade, bugbear, simplify)
- **Line-Length:** 120
- **Per-File-Ignores:** Tests dürfen Fixture-Re-Imports haben; `seeders.py` und `build*.py` dürfen lange Zeilen / `print()`.

```bash
python -m ruff check app tests          # nur prüfen
python -m ruff check --fix app tests    # auto-fixen (sicher)
python -m ruff format app tests         # formatieren
```

### Type-Check (Mypy)
- **Locker konfiguriert** — keine erzwungenen Annotations, aber `check_untyped_defs=true`.
- Third-Party-Module ohne Stubs (`alembic`, `webview`, `thefuzz`, `Levenshtein`, `openpyxl`, `reportlab`) sind in `[[tool.mypy.overrides]]` deaktiviert.

```bash
python -m mypy app
```

### Build-Logging
`build_logging.setup_build_log(script_name)` aktiviert einen `stdout`/`stderr`-Tee in `logs/build_<script>_<timestamp>.log`. Eingebunden in `build.py`, `build_windows_standalone.py` und `excel_import.py`. Konsolen-Ausgabe bleibt unverändert; bei Fehlern liegt jetzt zusätzlich ein nachvollziehbares Logfile vor.

## 🐛 Häufige Probleme

### 1. "Foreign Key constraint failed" beim Recipe-Löschen
**Ursache:** Recipe ist in MealPlan referenziert
**Lösung:** Erst MealPlans löschen oder Cascade-Delete zu Recipe.meal_plans hinzufügen

### 2. Camp-Auswahl wird nicht gespeichert
**Check:** Cookie `current_camp_id` und AppSettings `last_selected_camp_id`
**Fix:** `crud.set_setting(db, "last_selected_camp_id", str(camp_id))`

### 3. Einkaufsliste ist leer
**Ursache:** Kein Camp ausgewählt oder keine MealPlans vorhanden
**Debug:** `calculate_shopping_list()` gibt `{}` zurück wenn keine MealPlans

### 4. Unit-Konvertierung funktioniert nicht
**Hinweis:** Nur g/kg und ml/L werden automatisch konvertiert
**Custom Units:** Müssen in `unit_converter.py` ergänzt werden

## 🔍 Schnellreferenz für Änderungen

### Neues Datenbankfeld hinzufügen
1. `models.py` → Feld zu Modell hinzufügen
2. **Alembic-Migration generieren:** `alembic revision --autogenerate -m "add field xy"` (Pflicht, sonst bleibt User-DB veraltet — siehe „Datenbank-Migrationen")
3. Generiertes Skript in `alembic/versions/` prüfen und ggf. korrigieren (SQLite-Fallen!)
4. (Optional) `schemas.py` → Pydantic-Schema aktualisieren
5. (Optional) `crud.py` → CRUD-Funktionen anpassen
6. Lokal testen: `alembic upgrade head && alembic downgrade -1 && alembic upgrade head`

### Neuer API-Endpoint
1. Passenden Router in `app/routers/` wählen
2. Endpoint mit `@router.get/post/put/delete()` definieren
3. In `main.py` → `app.include_router()` (meist schon vorhanden)

### Neue Berechnung/Business-Logic
1. In `app/services/` neue Funktion schreiben
2. Von Router/Endpoint aufrufen

### UI-Änderung
1. Template in `app/templates/` bearbeiten
2. CSS: In Template via Tailwind-Klassen (oder eigene Klasse in `static/css/custom.css`)
3. Interaktivität:
   - HTMX-Attribute (`hx-get`, `hx-post`, ...) für Server-getriebene Updates
   - Alpine.js (`x-data`, `x-show`, `x-model`, ...) für Client-State
   - Größere Alpine-Komponenten in `app/static/js/` ablegen, nicht inline (Beispiel: `recipe-form.js`)
4. Wiederkehrende Form-Felder über Macros aus `components/forms.html` einbinden
5. Icon-only Buttons brauchen `aria-label`; rein dekorative SVGs `aria-hidden="true"`

---

---

## HTMX-Konventionen (Response-Pattern)

| Situation | Response-Typ |
|---|---|
| HTMX-DELETE ohne Rückgabe | `HTMLResponse(content="", status_code=200)` |
| HTMX-Aktion mit anschließendem Full-Reload | `Response(headers={"HX-Refresh": "true"})` |
| HTMX-Aktion mit gezielter Weiterleitung | `Response(headers={"HX-Redirect": "/ziel"})` |
| Form-POST mit Seitenwechsel | `RedirectResponse(url="/ziel", status_code=303)` |
| Partielle HTML-Rückgabe | `HTMLResponse(content=html_snippet)` |

## 📋 Story-Referenzen (v1.4.0)

Die fünf User Stories aus [USER_STORIES.md](USER_STORIES.md) sind in dieser Version umgesetzt:

| Story | Backend | Migration | UI-Touchpoints | Tests |
|---|---|---|---|---|
| **1: custom_servings** | `models.py`, `schemas.py`, `services/calculation.py`, `routers/export.py` (Recipe-Book) | `004` | `meal_planning/index.html` (Badge, Edit-Button via Prompt) | `test_meal_plan_custom_servings.py` |
| **2: Shopping-Notes + kompakte PDF** | `models.py` (`Ingredient.note`, `ShoppingListNote`), `crud.py`, `services/calculation.py`, `routers/shopping_list.py`, `routers/export.py` | `003` | `shopping_list.html` (Input pro Item, Badge für globale Note), `FreizeitApp.saveShoppingListNote` | `test_shopping_notes.py` |
| **3: Tageslisten-PDF + sub_category** | `constants.MEAL_SUB_CATEGORIES`, `models.py`, `schemas.py` (Validator), `routers/export.py` | `005` | `meal_planning/index.html` (Sub-Cat-Badge für DINNER, neuer FAB "Tageslisten") | `test_export_daily_lists.py` |
| **4: Rezept-Vorschau-Modal** | `routers/recipes.py` (`GET /recipes/{id}/preview`) | – | `templates/recipes/preview_modal.html`, Click-Handler auf `recipe-card-planned` mit Drag-Suppression | `test_recipe_preview.py` |
| **5: Reste-Tracker** | `models.Leftover`, `crud.py`, `services/leftover_statistics.py`, `routers/leftovers.py`, `main.py` (Router-Registrierung) | `006` | `base.html` (Sidebar-Link), `meal_planning/index.html` ("Reste erfassen"-Button), `templates/leftovers/*` | `test_leftovers.py` |

**🤖 AI-Hinweis:** Dieses Dokument priorisiert **Geschwindigkeit** und **Token-Effizienz**. Für tiefe Analysen siehe `ANALYSE.md`. Bei Unklarheiten: Code in `app/` ist gut dokumentiert!
