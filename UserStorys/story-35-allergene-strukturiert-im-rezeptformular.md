# Story 35: Allergene strukturiert im Rezeptformular auswählen

**Status:** Done
**Aufwand:** Klein-Mittel
**Machbarkeit:** Sehr gut
**Implementiert in:** `app/routers/recipes.py:23-31,65-75,78-110,182-235` (Allergen-Context + `allergen_ids` in POST/PUT, `allergen_notes` aus Form entfernt), `app/templates/recipes/_form.html:406-425` (Checkbox-Block), `app/static/js/recipe-form.js:168,358-370` (`allergen_ids` in formData + Submit), `app/templates/recipes/edit.html:46-60` (initialData), `app/templates/recipes/detail.html:108-109` (Freitext-Block entfernt), `tests/test_recipe_allergens.py`
**Abhängigkeit:** [Story 33](story-33-allergene-in-einstellungen-verwalten.md) — benötigt eine in den Einstellungen gepflegte Allergen-Liste als Auswahlquelle.

## Beschreibung

Als Küchenplaner möchte ich beim Bearbeiten eines Rezepts Allergene aus einer gepflegten Liste auswählen — genau wie Tags — statt sie als Freitext einzugeben, damit Allergene strukturiert erfasst und in Listen/Exporten ausgegeben werden können.

## Ist-Zustand

- `app/templates/recipes/_form.html:384-404` — Tags als Checkbox-Badges (`x-model="formData.tag_ids"`).
- `app/templates/recipes/_form.html:406-418` — Allergene aktuell **nur Freitext** (`allergen_notes`-Textarea).
- `app/schemas.py:151-192` — Recipe-Schema hat bereits `allergens: list[Allergen]` und `allergen_ids: list[int]`; M:N-Relation `app/models.py:91`.
- `app/static/js/recipe-form.js:167,369` — `formData.tag_ids` wird als JSON gesendet (`JSON.stringify(this.formData.tag_ids)`) — Muster für `allergen_ids`.
- `app/routers/settings.py:96` — `get_allergens(db)` existiert als Quelle der Allergen-Liste.

## Akzeptanzkriterien

- [x] Im Rezeptformular werden Allergene als Checkbox-Badges aus der Allergen-Liste angeboten (analog Tags), gebunden an `formData.allergen_ids`.
- [x] Das Freitext-Feld „Allergen-Hinweise" (`allergen_notes`) wird aus dem Formular **entfernt** (Entscheidung: nur strukturierte Auswahl).
- [x] Beim Speichern werden `allergen_ids` korrekt persistiert — sowohl beim Anlegen als auch beim Bearbeiten.
- [x] Beim Bearbeiten eines Rezepts sind die bereits gesetzten Allergene vorausgewählt.
- [x] Die Allergen-Liste wird in den Create-/Edit-Context übergeben (analog zur `tags`-Übergabe).
- [x] Pytest deckt ab: Recipe-Create/-Update mit `allergen_ids` setzt die M:N-Verknüpfung korrekt; die Detailseite zeigt die strukturierten Allergene.

## Technische Umsetzung (Vorschlag)

### Backend

- `app/routers/recipes.py` — Allergen-Liste (`crud.get_allergens(db)`) in den Context der Create- und Edit-Routen geben (analog `tags`); sicherstellen, dass `allergen_ids` beim Anlegen/Bearbeiten verarbeitet und an die M:N-Relation durchgereicht wird (`crud` Recipe-Create/-Update).

### Frontend

- `app/templates/recipes/_form.html` — Allergen-Checkbox-Block analog zum Tags-Block (`:388-402`) ergänzen, gebunden an `formData.allergen_ids`; den `allergen_notes`-Block (`:406-418`) entfernen.
- `app/static/js/recipe-form.js` — `allergen_ids` in `formData` initialisieren, beim Submit als JSON anhängen (analog `tag_ids`, `:369`); `allergen_notes`-Handling entfernen.
- `app/templates/recipes/detail.html` — strukturierte Allergene anzeigen (der bisherige Freitext-Block entfällt).

### Hinweise

- Die Spalte `Recipe.allergen_notes` bleibt vorerst im Modell erhalten (bestehende Daten gehen nicht verloren), wird aber nicht mehr im Formular gepflegt. Eine spätere Migration/Entfernung ist nicht Teil dieser Story.

### Tests

- `tests/` — Recipe-Create und -Update mit `allergen_ids` setzt/aktualisiert die M:N-Verknüpfung; Detailseite enthält die Allergen-Namen.
