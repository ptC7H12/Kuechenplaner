# Kuechenplaner - App-Übersicht

## Tech-Stack
- **Backend:** Python FastAPI + SQLAlchemy ORM + SQLite
- **Frontend:** Jinja2 Templates + HTMX + Alpine.js + Tailwind CSS
- **Desktop:** pywebview (Desktop-Fenster um die Web-App)
- **PDF-Export:** ReportLab
- **Excel-Export:** openpyxl
- **Drag & Drop:** SortableJS
- **Build:** Nuitka (standalone Windows-Executable)

## Projektstruktur

```
app/
├── main.py                    # FastAPI Entry Point, Dashboard, Camp-Auswahl
├── models.py                  # SQLAlchemy Models (Camp, Recipe, Ingredient, MealPlan, etc.)
├── crud.py                    # Datenbankoperationen (40+ Funktionen)
├── schemas.py                 # Pydantic Validierung
├── database.py                # SQLite Setup (WAL-Modus)
├── dependencies.py            # FastAPI Dependencies (Camp-Auswahl via Cookie)
├── services/
│   ├── calculation.py         # Rezept-Skalierung, Einkaufsliste, Camp-Statistiken
│   └── unit_converter.py      # Einheitenumrechnung (g→kg, ml→L)
├── routers/
│   ├── camps.py               # Camp-Verwaltung (CRUD)
│   ├── recipes.py             # Rezept-Verwaltung (CRUD + Fuzzy-Suche)
│   ├── meal_planning.py       # Mahlzeitenplanung (Kalender + Drag&Drop API)
│   ├── shopping_list.py       # Einkaufsliste (Berechnung + Anzeige)
│   ├── export.py              # PDF/Excel Export (Einkaufsliste, Speiseplan, Rezeptbuch)
│   ├── allergens.py           # Allergen-Verwaltung
│   └── settings.py            # Einstellungen/Import
├── templates/
│   ├── base.html              # Layout mit Sidebar-Navigation
│   ├── dashboard.html         # Statistiken-Übersicht
│   ├── camp_select.html       # Camp-Auswahl
│   ├── recipes/               # Rezept-Templates (Liste, Detail, Formular)
│   ├── meal_planning/         # Kalender-Grid mit Drag&Drop
│   ├── shopping_list.html     # Einkaufsliste
│   └── components/            # Wiederverwendbare Komponenten
└── static/                    # CSS, Icons
```

## Datenmodell

### Camp
- `name`, `start_date`, `end_date`, `participant_count`
- Die Teilnehmerzahl wird global für alle Rezepte zur Skalierung verwendet

### Recipe
- `name`, `description`, `base_servings` (Standard: 30), `instructions`
- `preparation_time`, `cooking_time`, `allergen_notes`, `image_path`
- Versionierung über `RecipeVersion` (JSON-Snapshots)

### MealPlan
- Verknüpft Camp + Recipe + Datum + Mahlzeittyp (Frühstück/Mittag/Abend)
- `position` für mehrere Rezepte pro Slot, `notes` für Anmerkungen
- Unique Constraint: (camp_id, meal_date, meal_type, position)

### Ingredient / RecipeIngredient
- Zutaten mit Kategorie, Einheit
- Mengenangabe pro Rezept über Verknüpfungstabelle

## Kernfunktionen

### Mahlzeitenplanung
- Kalender-Grid: Alle Tage des Camps × 3 Mahlzeiten
- Drag & Drop von Rezepten aus Sidebar in Kalender-Slots
- "Kein Essen"-Marker für bewusst leere Slots
- Kopieren von Mahlzeiten auf andere Tage

### Rezept-Skalierung
- Formel: `scaling_factor = camp.participant_count / recipe.base_servings`
- Wird bei Einkaufsliste und Rezeptbuch automatisch angewendet
- Einheitenumrechnung: g→kg (>1000g), ml→L (>1000ml)

### PDF-Exporte
1. **Einkaufsliste** - Aggregiert alle Zutaten, skaliert, nach Kategorie gruppiert
2. **Speiseplan** - Landscape-Tabelle mit Tagen × Mahlzeiten (10 Tage/Seite)
3. **Rezeptbuch** - Alle Rezepte eines Camps mit skalierten Mengen
4. **Rezeptsammlung** - Alle Rezepte mit Inhaltsverzeichnis (unskaliert)

### Excel-Export
- Einkaufsliste mit Kategorien, Mengen, Einheiten und Checkbox-Spalte

## Navigation
| Route | Funktion |
|---|---|
| `/select-camp` | Camp auswählen |
| `/dashboard` | Statistiken |
| `/recipes/` | Rezeptliste |
| `/meal-planning/` | Kalender/Wochenübersicht |
| `/shopping-list/` | Einkaufsliste |
| `/export/...` | PDF/Excel Exporte |
