# TECHNICAL README - Kuechenplaner
> **Quick Reference für AI-Assistenten** | Zuletzt aktualisiert: 2025-12-11

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
│   ├── database.py          # DB-Setup, Session-Management
│   ├── dependencies.py      # FastAPI-Dependencies (get_current_camp, etc.)
│   ├── routers/             # API-Endpunkte (siehe API-Referenz)
│   │   ├── camps.py         # /api/camps/*
│   │   ├── recipes.py       # /recipes/*
│   │   ├── allergens.py     # /api/allergens/*
│   │   ├── meal_planning.py # /meal-planning/*
│   │   ├── shopping_list.py # /shopping-list/*
│   │   ├── export.py        # /export/* (PDF, Excel)
│   │   └── settings.py      # /settings/*
│   ├── services/
│   │   ├── calculation.py   # Skalierung, Einkaufslisten-Berechnung
│   │   └── unit_converter.py # g↔kg, ml↔L Konvertierung
│   ├── templates/           # Jinja2-Templates (HTMX)
│   └── static/              # CSS, Icons
├── alembic/                 # DB-Migrations (konfiguriert, aber leer)
├── requirements.txt         # Python-Dependencies
└── build.py                 # Nuitka-Build für Standalone-Exe
```

## 🗄️ Datenmodell (models.py)

### Kern-Entitäten
| Tabelle | Beschreibung | Wichtige Felder |
|---------|-------------|-----------------|
| **Camp** | Freizeit/Veranstaltung | `name`, `start_date`, `end_date`, `participant_count` |
| **Recipe** | Global wiederverwendbare Rezepte | `name`, `base_servings`, `version_number` |
| **Ingredient** | Zutat-Stammdaten | `name`, `unit`, `category` (z.B. "Gemüse") |
| **RecipeIngredient** | Zutat in Rezept (M:N) | `recipe_id`, `ingredient_id`, `quantity`, `unit` |
| **MealPlan** | Rezept zu Mahlzeit zugeordnet | `camp_id`, `recipe_id`, `meal_date`, `meal_type`, `position` |
| **Tag** | Kategorien (M:N zu Recipe) | `name`, `color`, `icon` (z.B. "Frühstück" 🌅) |
| **Allergen** | Allergene (M:N zu Recipe) | `name`, `icon` (z.B. "Gluten" 🌾) |
| **RecipeVersion** | Rezept-Snapshots | `recipe_id`, `version_number`, `ingredients_snapshot` (JSON) |
| **AppSettings** | Key-Value-Store | `key`, `value` (JSON) |

### MealType Enum
```python
class MealType(enum.Enum):
    BREAKFAST = "BREAKFAST"
    LUNCH = "LUNCH"
    DINNER = "DINNER"
```

### Wichtige Constraints
- **Camp:** `start_date <= end_date`, `participant_count > 0`
- **MealPlan:** UNIQUE(`camp_id`, `meal_date`, `meal_type`, `position`)
- **RecipeVersion:** UNIQUE(`recipe_id`, `version_number`)

### Beziehungen
```
Camp 1───N MealPlan N───1 Recipe
                          ├─N RecipeIngredient N─1 Ingredient
                          ├─N Tag (M:N)
                          ├─N Allergen (M:N)
                          └─N RecipeVersion
```

## 🔌 API-Endpunkte (Auswahl)

### Camps (`/api/camps/`)
- `GET /api/camps/` - Alle Freizeiten
- `POST /api/camps/` - Neue Freizeit
- `PUT /api/camps/{id}` - Freizeit bearbeiten
- `DELETE /api/camps/{id}` - Freizeit löschen (CASCADE: löscht alle MealPlans!)
- `POST /api/camps/{id}/select` - Freizeit auswählen (setzt Cookie)

### Recipes (`/recipes/`)
- `GET /recipes/` - Rezept-Liste (HTML)
- `POST /recipes/create` - Neues Rezept
- `PUT /recipes/{id}` - Rezept bearbeiten (**erstellt neue Version**)
- `DELETE /recipes/{id}` - Rezept löschen
- `GET /recipes/search` - Suche & Filter (`?search=...&tag_ids=...`)

### Meal Planning (`/meal-planning/`)
- `GET /meal-planning/` - Kalender-Ansicht
- `POST /meal-planning/add` - Rezept zu Mahlzeit hinzufügen
- `DELETE /meal-planning/{id}` - Mahlzeit entfernen
- `PUT /meal-planning/{id}/move` - Mahlzeit verschieben

### Shopping List (`/shopping-list/`)
- `GET /shopping-list/` - Einkaufsliste (HTML)
- `GET /shopping-list/api/generate` - Berechnete Liste (JSON)
- `POST /shopping-list/api/check/{ingredient_id}` - Zutat abhaken

### Export (`/export/`)
- `GET /export/shopping-list/pdf` - Einkaufsliste als PDF
- `GET /export/shopping-list/excel` - Einkaufsliste als Excel
- `GET /export/meal-plan/pdf` - Mahlzeitenplan als PDF

## ⚙️ Wichtige Services

### `services/calculation.py`
**Funktionen:**
- `calculate_shopping_list(db, camp_id)` → Aggregierte Einkaufsliste
  - Lädt alle MealPlans für Camp
  - Skaliert Rezepte auf `camp.participant_count`
  - Aggregiert Zutaten nach `ingredient_id`
  - Konvertiert Einheiten (g→kg, ml→L)
  - Gruppiert nach `category`
- `get_camp_statistics(db, camp_id)` → Dashboard-Statistiken

### `services/unit_converter.py`
**Konvertierungen:**
- `convert_unit(quantity, from_unit, to_unit)`
  - g ↔ kg (1000:1)
  - ml ↔ L (1000:1)
  - TL ↔ EL (3:1)
- **Best-Unit-Auswahl:** `>= 1000g` → `kg`, `>= 1000ml` → `L`

## 🎨 Frontend-Architektur

### Technologien
- **Templates:** Jinja2 (`app/templates/`)
- **Interaktivität:** HTMX (partielle Updates ohne JS)
- **Styling:** Tailwind CSS
- **Icons:** Emoji + Heroicons

### Template-Struktur
```
templates/
├── base.html                # Layout, Navigation
├── dashboard.html           # Startseite mit Statistiken
├── camp_select.html         # Freizeit-Auswahl
├── recipes/
│   ├── list.html           # Rezept-Übersicht
│   ├── create.html         # Rezept-Formular
│   └── partials/           # HTMX-Fragmente
├── meal_planning/
│   └── index.html          # Kalender-Grid (Drag & Drop TODO)
└── components/             # Wiederverwendbare UI-Komponenten
```

### HTMX-Muster
```html
<!-- Beispiel: Rezept-Suche -->
<input hx-get="/recipes/search"
       hx-trigger="keyup changed delay:300ms"
       hx-target="#recipe-list">
```

## 🔑 Wichtige Konzepte

### 1. Camp-Auswahl-Mechanismus
- **Cookie:** `current_camp_id` speichert aktuelles Camp
- **Dependency:** `get_current_camp(request)` in `dependencies.py`
- **Persistenz:** AppSettings `last_selected_camp_id`

### 2. Rezept-Skalierung
```python
# Rezept mit base_servings=30 für Camp mit 45 Teilnehmern
scaling_factor = camp.participant_count / recipe.base_servings  # 1.5
scaled_quantity = ingredient.quantity * scaling_factor
```

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
# Dependencies installieren
pip install -r requirements.txt

# Dev-Server starten (Port 12000)
DEVELOPMENT=1 python -m app.main

# Datenbank-Migration erstellen (aktuell nicht verwendet)
alembic revision --autogenerate -m "message"
alembic upgrade head
```

### Build (Standalone Windows)
```bash
python build_windows_standalone.py
```

### Wichtige Befehle
```bash
# DB neu erstellen (Achtung: Datenverlust!)
rm kuechenplaner.db  # DB-Datei löschen
python -m app.main   # Neu erstellen bei Startup

# Excel-Import (siehe excel_import.py)
python excel_import.py recipes.xlsx
```

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

## 📊 Status & TODOs

### ✅ Implementiert
- Camp-Verwaltung (CRUD)
- Rezept-Verwaltung (CRUD + Versionierung)
- Dashboard mit Statistiken
- Einkaufslisten-Berechnung (Backend)
- Allergen- & Tag-System
- Unit-Konvertierung

### 🟡 Teilweise
- Meal-Planning (Backend OK, Drag & Drop UI fehlt)
- Shopping-List (Berechnung OK, UI fehlt)
- Export (PDFs/Excel TODO)

### ❌ TODO
- Drag & Drop UI für Meal-Planning
- Export-Funktionen (PDFs, Excel)
- Recipe-Edit UI (Backend vorhanden)
- Settings-UI
- Rezept-Bilder
- Alembic-Migrations nutzen

Siehe **ANALYSE.md** für detaillierte Roadmap!

## 🔍 Schnellreferenz für Änderungen

### Neues Datenbankfeld hinzufügen
1. `models.py` → Feld zu Modell hinzufügen
2. (Optional) `schemas.py` → Pydantic-Schema aktualisieren
3. (Optional) `crud.py` → CRUD-Funktionen anpassen
4. **WICHTIG:** DB neu erstellen oder Alembic-Migration schreiben

### Neuer API-Endpoint
1. Passenden Router in `app/routers/` wählen
2. Endpoint mit `@router.get/post/put/delete()` definieren
3. In `main.py` → `app.include_router()` (meist schon vorhanden)

### Neue Berechnung/Business-Logic
1. In `app/services/` neue Funktion schreiben
2. Von Router/Endpoint aufrufen

### UI-Änderung
1. Template in `app/templates/` bearbeiten
2. CSS: In Template via Tailwind-Klassen
3. Interaktivität: HTMX-Attribute (`hx-get`, `hx-post`, etc.)

---

**🤖 AI-Hinweis:** Dieses Dokument priorisiert **Geschwindigkeit** und **Token-Effizienz**. Für tiefe Analysen siehe `ANALYSE.md`. Bei Unklarheiten: Code in `app/` ist gut dokumentiert!
