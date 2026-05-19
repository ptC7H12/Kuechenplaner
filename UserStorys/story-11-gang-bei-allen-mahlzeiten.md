# Story 11: "+Gang" Button bei allen Mahlzeiten

**Status:** Done
**Aufwand:** Sehr klein
**Machbarkeit:** Sehr gut
**Implementiert in:** `app/templates/meal_planning/index.html:235` (Bedingung entfernt, Button erscheint für BREAKFAST/LUNCH/DINNER), `app/routers/export.py:565-567` (Sub-Category Sortier-Logik)

## Beschreibung

Als Küchenplaner möchte ich auch beim Frühstück und Mittagessen Sub-Kategorien (Gänge) vergeben können, damit ich z.B. süß + herzhaft beim Frühstück oder Suppe + Hauptgang + Nachtisch beim Mittag strukturieren kann.

## Ist-Zustand

- `app/templates/meal_planning/index.html:225` schränkt den "+Gang"-Button auf Abendessen ein: `{% if meal_plan.recipe_id and meal_type_value == 'DINNER' %}`
- Sub-Category-Daten und API-Logik (`PUT /meal-planning/api/meal-plans/{id}`) sind bereits für alle Mahlzeiten lauffähig — nur die UI versteckt das Feature
- Decision aus Story 3 ("Sub-Kategorien nur beim Abendessen") wird hiermit revidiert

## Akzeptanzkriterien

- [x] Der "+Gang"-Button erscheint bei Frühstück, Mittagessen und Abendessen
- [x] Die Sub-Category-Werte (`Vorspeise`, `Hauptgang`, `Beilage`, `Salat`, `Nachtisch`) aus `app/constants.py:9` bleiben unverändert
- [x] Die Tagesliste-PDF-Sortierung (`export.py:550-552`) sortiert auch Frühstück + Mittag nach Sub-Category, wenn gesetzt
- [x] Bestehender DB-Spaltenwert `meal_plans.sub_category` bleibt unverändert

## Technische Umsetzung

- In `app/templates/meal_planning/index.html:225` die Bedingung `meal_type_value == 'DINNER'` entfernen
- In `app/routers/export.py:550-552` die Sortier-Logik so erweitern, dass sie für alle Meal-Types nach Sub-Category gruppiert (falls nicht schon der Fall)

## Hinweis

- Wenn ein Nutzer keine Sub-Categories beim Frühstück braucht, ignoriert er den Button — er bleibt grau im "+ Gang"-Zustand. Kein erzwungener Workflow.
