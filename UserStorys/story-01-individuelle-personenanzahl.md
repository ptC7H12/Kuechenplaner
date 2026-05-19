# Story 1: Individuelle Personenanzahl pro Rezept im Mahlzeitenplan

**Status:** Done
**Aufwand:** Mittel
**Machbarkeit:** Gut
**Implementiert in:** `app/models.py` (`MealPlan.custom_servings`), `alembic/versions/004_meal_plan_custom_servings.py`, `app/services/calculation.py`, `app/templates/meal_planning/servings_modal.html`, Endpunkt `PUT /meal-planning/api/meal-plans/{id}`, `tests/test_meal_plan_custom_servings.py`

## Beschreibung

Als Küchenplaner möchte ich für einzelne Rezepte im Mahlzeitenplan eine abweichende Personenanzahl angeben können, damit ich flexibel planen kann, wenn z.B. beim Frühstück weniger Leute essen als beim Mittagessen.

## Ist-Zustand

- `participant_count` liegt auf dem **Camp** (global für alle Mahlzeiten)
- Skalierung: `camp.participant_count / recipe.base_servings`
- Kein Override pro MealPlan-Eintrag möglich

## Akzeptanzkriterien

- [x] Jeder MealPlan-Eintrag hat ein optionales Feld `custom_servings`
- [x] Wenn `custom_servings` gesetzt ist, wird dieses statt `camp.participant_count` für die Skalierung verwendet
- [x] In der Wochenübersicht ist die abweichende Personenanzahl sichtbar (z.B. kleiner Badge)
- [x] Beim Drag & Drop eines Rezepts kann optional eine Personenanzahl eingegeben werden
- [x] Die Einkaufsliste berücksichtigt die individuellen Personenanzahlen korrekt
- [x] Der PDF-Export (Rezeptbuch) zeigt die korrekte Personenanzahl pro Rezept

## Technische Umsetzung

- `MealPlan.custom_servings` (Integer, nullable) in `models.py` hinzufügen
- `calculation.py` → `calculate_shopping_list()` anpassen: `custom_servings or camp.participant_count`
- UI: Kleines Eingabefeld oder Popup beim Platzieren/Bearbeiten eines Rezepts
- Alle Export-Funktionen in `export.py` anpassen

## Hinweise

- Standardverhalten bleibt: Ohne Override gilt weiterhin `camp.participant_count`
- DB-Migration nötig (neues Feld in `meal_plans` Tabelle)
