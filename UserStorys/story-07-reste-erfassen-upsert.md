# Story 7: Reste-Erfassen aktualisieren statt duplizieren

**Status:** Done
**Aufwand:** Klein-Mittel
**Machbarkeit:** Sehr gut
**Implementiert in:** `app/routers/leftovers.py:71` (Endpunkt `GET /leftovers/api/by-meal-plan/{meal_plan_id}`), `app/templates/meal_planning/index.html:229-232` (Indikator-Badge, Farb-Toggle orange-700 wenn erfasst)

## Beschreibung

Als Küchenplaner möchte ich beim erneuten Klick auf "Reste erfassen" für eine bereits erfasste Mahlzeit den bestehenden Eintrag bearbeiten, statt einen Duplikat anzulegen, damit meine Statistik sauber bleibt.

## Ist-Zustand

- Der "Reste erfassen"-Button im Speiseplan (`meal_planning/index.html:209-216`) öffnet immer `/leftovers/new?meal_plan_id={id}` und erzeugt per POST einen neuen Eintrag
- Es gibt keinen GET-Endpunkt, der einen bestehenden Eintrag pro `meal_plan_id` zurückgibt
- Folge: Jeder erneute Klick erzeugt einen Duplikat in `leftovers` — Statistik verzerrt sich

## Akzeptanzkriterien

- [x] Beim Öffnen des Reste-Modals werden vorhandene Werte für diese Mahlzeit ins Formular vorgeladen
- [x] Speichern eines bereits erfassten Restes führt zu PUT statt POST (Update statt Insert)
- [x] Der "Reste erfassen"-Icon in der Wochenübersicht wird visuell unterschieden, wenn bereits Reste erfasst sind (z.B. gefülltes Icon oder kleines Badge mit %-Wert)
- [x] Keine Duplikate mehr in `leftovers`-Tabelle pro `meal_plan_id`

## Technische Umsetzung

- Neuer Endpunkt `GET /leftovers/api/by-meal-plan/{meal_plan_id}` in `app/routers/leftovers.py` → liefert vorhandenen Eintrag oder 404
- `app/templates/leftovers/new_modal.html`: Beim Mount via HTMX/Alpine.js den bestehenden Eintrag laden und Formular vorbefüllen
- Form-Submit: Wenn `id` vorhanden → PUT `/leftovers/api/leftovers/{id}`, sonst POST
- In `meal_planning/index.html`: Indikator-Badge oder Icon-Farbwechsel basierend auf `meal_plan.leftover` (Relation muss im Template verfügbar sein)
