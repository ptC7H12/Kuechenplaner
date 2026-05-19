# Story 15: Verfügbare Rezepte in Speiseplan-Sidebar alphabetisch A-Z

**Status:** Done
**Aufwand:** Sehr klein
**Machbarkeit:** Sehr gut
**Implementiert in:** `app/crud.py:70` (`order_by` Parameter), `app/routers/meal_planning.py:36` (`order_by="name"`), `.collate("NOCASE").asc()` für Umlaute

## Beschreibung

Als Küchenplaner möchte ich, dass die Liste der verfügbaren Rezepte im Speiseplan alphabetisch sortiert ist (A→Z), damit ich Rezepte schnell finde.

## Ist-Zustand

- Sidebar `Verfügbare Rezepte` in `app/templates/meal_planning/index.html:57-81` zeigt Rezepte in der Reihenfolge der `get_recipes()`-Query
- `app/crud.py:77` sortiert per Default nach `models.Recipe.updated_at.desc()` (neueste Bearbeitung zuerst)
- Aus Sicht des Users wirkt das wie "Z→A", weil neu angelegte Rezepte oft unten im Alphabet sind oder weil die Reihenfolge intransparent ist

## Akzeptanzkriterien

- [x] **Nur die Speiseplan-Sidebar** sortiert alphabetisch nach Rezeptname (A→Z)
- [x] Die Rezeptübersicht (`/recipes`) behält ihre bisherige "zuletzt bearbeitet zuerst"-Sortierung (damit man eigene neue Rezepte oben sieht)
- [x] Umlaute werden korrekt sortiert (`Ä` neben `A`, nicht ans Ende), via `collate("NOCASE")` oder Equivalent
- [x] Keine Breaking Changes für andere `get_recipes()`-Aufrufer

## Technische Umsetzung

- `app/crud.py:64-77` `get_recipes()` um optionalen Parameter `order_by: str = "updated_at"` erweitern (Werte: `"updated_at"`, `"name"`)
- Im meal-planning Router (`app/routers/meal_planning.py`) beim Sidebar-Laden `order_by="name"` setzen
- SQLAlchemy: `models.Recipe.name.collate("NOCASE").asc()` für umlautsichere Sortierung
- Recipe-Index-Route ruft `get_recipes()` weiterhin mit Default auf — bleibt unverändert
