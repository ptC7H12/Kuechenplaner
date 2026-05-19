# Story 12: Schöne Popups für Personenanzahl und Gang

**Status:** Done
**Aufwand:** Klein
**Machbarkeit:** Sehr gut
**Implementiert in:** `app/templates/meal_planning/servings_modal.html`, `app/templates/meal_planning/sub_category_modal.html`, `app/routers/meal_planning.py:143,159` (Endpunkte für Modal-Templates), keine `prompt()` mehr in JS, Modal-Pattern via `window.FreizeitApp.openModal()`

## Beschreibung

Als Küchenplaner möchte ich beim Klick auf "Personenanzahl" und "+Gang" im Speiseplan einen gestylten Dialog im App-Design öffnen, nicht den hässlichen Browser-`prompt()`.

## Ist-Zustand

- `editServings()` in `meal_planning/index.html:303-334` nutzt `prompt()` für die Personenanzahl-Eingabe
- `editSubCategory()` in `meal_planning/index.html:277-301` nutzt `prompt()` mit Optionsliste als Text
- Beides ist nicht stylebar, sieht in Browsern unterschiedlich aus, ist auf Mobile suboptimal

## Akzeptanzkriterien

- [x] Klick auf das Person-Icon öffnet ein Modal mit `<input class="form-input" type="number">` + Speichern/Standard verwenden/Abbrechen-Buttons
- [x] Klick auf "+Gang" öffnet ein Modal mit einer Button-Liste der Kategorien aus `app/constants.py:9` + Entfernen-Button
- [x] Beide Modals nutzen exakt das gleiche Pattern wie `leftovers/new_modal.html` (globales Modal + `window.FreizeitApp.openModal()`)
- [x] Speichern via PUT `/meal-planning/api/meal-plans/{id}` (Endpunkt bereits vorhanden)
- [x] Keine `prompt()`-Aufrufe mehr in `meal_planning/index.html`
- [x] Ausschließlich bestehende CSS-Klassen (`.btn`, `.btn-primary`, `.btn-secondary`, `.btn-icon`, `.form-input`, `.form-label`) — keine neuen Styles

## Technische Umsetzung

- Neue Templates: `app/templates/meal_planning/servings_modal.html` und `app/templates/meal_planning/sub_category_modal.html` — Struktur exakt wie `leftovers/new_modal.html`
- Trigger via `window.FreizeitApp.openModal('/meal-planning/servings-modal/{meal_plan_id}')` (Modal-Pattern aus `base.html:186-197`)
- Endpunkte im `meal_planning`-Router, die die Modal-Templates ausliefern
- `editServings()` und `editSubCategory()` in `meal_planning/index.html` reduzieren sich auf einen `openModal()`-Aufruf
