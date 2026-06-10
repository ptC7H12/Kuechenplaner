# Story 39: Zutaten-Kategorie im Rezeptformular bearbeiten

**Status:** Done
**Aufwand:** Mittel
**Machbarkeit:** Gut
**Implementiert in:** `app/routers/recipes.py:23-60` (parse + `apply_ingredient_category_updates`), `app/routers/recipes.py:71-114,201-243` (Kategorien-Context + Updates bei create/update), `app/routers/recipes.py:305-360` (search/quick-create `category_id`), `app/static/js/recipe-form.js:43-56,199-215,269-301,315-330,360-371` (category_id durchreichen + `onIngredientCategoryChange`), `app/templates/recipes/_form.html:315-335` (Kategorie-Select pro Zeile), `app/templates/recipes/create.html`, `app/templates/recipes/edit.html` (`RECIPE_FORM_CONFIG.categories`), `tests/test_recipe_ingredient_category.py`
**Abhängigkeit:** [Story 30](story-30-zutatenkategorien-manuell.md) — nutzt die dort eingeführte `categories`-Tabelle, `Ingredient.category_id` und `crud.update_ingredient`.

## Beschreibung

Als Küchenplaner möchte ich beim Bearbeiten eines Rezepts die Kategorie einer Zutat sehen und ändern können; wenn ich eine Zutat per Fuzzy-Suche auswähle, soll die hinterlegte Kategorie übernommen werden — diese muss ich anschließend aber noch ändern können —, damit Zutaten in der Einkaufsliste korrekt gruppiert werden.

## Ist-Zustand

- `app/static/js/recipe-form.js:19-82` — `ingredientAutocomplete()`; der Fuzzy-Vorschlag enthält bereits `category` (`recipe-form.js:49`).
- `app/routers/recipes.py:293-311` — Such-Endpoint liefert den Kategorie-Namen mit (`:307`: `ingredient.category.name if ingredient.category else ""`).
- `app/static/js/recipe-form.js:269-301,315-317` — `addIngredient()` übernimmt `category` und gruppiert danach, bietet aber **kein editierbares Feld** für die Kategorie.
- `app/models.py:96-110` — `Ingredient.category_id` (FK → `categories.id`, `ondelete SET NULL`); `update_ingredient` aus Story 30 in `app/crud.py` vorhanden.
- `app/crud.py` — `get_or_create_ingredient` setzt die Kategorie nur beim Anlegen.

## Akzeptanzkriterien

- [x] Pro Zutat im Rezeptformular gibt es ein editierbares Kategorie-Feld (`<select>` der vorhandenen Kategorien aus Story 30).
- [x] Wählt man einen Fuzzy-Vorschlag, wird dessen Kategorie vorbelegt, bleibt aber änderbar.
- [x] Eine Kategorie-Änderung aktualisiert die **globale Zutat** (`ingredients`-Tabelle) und wirkt sich auf alle Rezepte und die Einkaufsliste aus; künftige Fuzzy-Vorschläge liefern die neue Kategorie.
- [x] Neue Zutaten ohne Vorschlag können eine Kategorie zugewiesen bekommen.
- [x] Pytest deckt ab: Eine Kategorie-Änderung über das Rezept-Formular persistiert an der Zutat (`update_ingredient`) und ist anschließend in der Fuzzy-Suche/Einkaufsliste sichtbar.

## Technische Umsetzung (Vorschlag)

### Backend

- `app/routers/recipes.py` — die Kategorien-Liste (`crud.get_categories(db)`) in den Form-Context (Create + Edit) geben; beim Speichern den gewählten Kategorie-Wert pro Zutat an `crud.update_ingredient` bzw. `get_or_create_ingredient` durchreichen, sodass die **globale** Zutat aktualisiert wird.
- `app/crud.py` — vorhandenes `update_ingredient` (Story 30) wiederverwenden; ggf. `get_or_create_ingredient` so erweitern, dass eine mitgegebene `category_id` auch bei bereits existierender Zutat gesetzt/aktualisiert wird.

### Frontend

- `app/templates/recipes/_form.html` + `app/static/js/recipe-form.js` — pro Zutatenzeile ein Kategorie-`<select>` (Optionsliste aus dem Context) ergänzen; bei Auswahl eines Fuzzy-Vorschlags die mitgelieferte `category` vorbelegen (`recipe-form.js:49`), aber editierbar lassen.
- Kein neues Override-Feld an der Rezept-Zutat-Verknüpfung (Entscheidung: globale Zutat wird aktualisiert).

### Tests

- `tests/` (Recipe-/Settings-Suite) — Kategorie-Änderung über das Rezept-Formular persistiert an der Zutat; danach liefert die Fuzzy-Suche die neue Kategorie und die Einkaufsliste gruppiert entsprechend.
