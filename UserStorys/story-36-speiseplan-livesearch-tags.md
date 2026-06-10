# Story 36: Speiseplan-Livesearch schließt Tags ein

**Status:** Done
**Aufwand:** Sehr klein
**Machbarkeit:** Sehr gut
**Implementiert in:** `app/templates/meal_planning/index.html:302-306` (`filterRecipes()` matcht jetzt Name + Tag-Namen)

## Beschreibung

Als Küchenplaner möchte ich im Speiseplan die Rezept-Suche auch über Tags ausführen — wie es der Hinweistext in den Einstellungen verspricht —, damit ich Rezepte schnell nach Tag finden kann.

## Ist-Zustand

- `app/templates/meal_planning/index.html:29-36` — Suchfeld mit Alpine-Binding `@input="filterRecipes()"`.
- `app/templates/meal_planning/index.html:294-307` — `filterRecipes()` filtert **nur** nach `recipe.name` (`'{{ recipe.name }}'.toLowerCase().includes(query)`); Tags sind ausgenommen.
- `app/templates/meal_planning/index.html:70-78` — Tags werden in der Sidebar pro Rezept bereits angezeigt, aber nicht durchsucht.
- Hintergrund: In den Einstellungen steht der Hinweis, dass Tags beim Filtern im Speiseplan helfen (siehe Story 30) — das greift aktuell nicht.

## Akzeptanzkriterien

- [x] Die Livesearch im Speiseplan matcht zusätzlich gegen die Tag-Namen jedes Rezepts.
- [x] Treffer per Rezeptname **oder** Tag-Name werden angezeigt; die Suche bleibt case-insensitiv und flüssig.
- [x] Die clientseitige Filterung bleibt erhalten (kein zusätzlicher Server-Roundtrip) — die Tag-Namen werden als Datenattribut/Datenfeld bereitgestellt.

## Technische Umsetzung (Vorschlag)

### Frontend

- `app/templates/meal_planning/index.html` — pro Rezeptkarte die Tag-Namen als Datenattribut rendern (z. B. `data-tags="{{ recipe.tags | map(attribute='name') | join(' ') | lower }}"`) oder in das Alpine-Datenobjekt der Karte aufnehmen.
- `filterRecipes()` (`:294-307`) so erweitern, dass der Query gegen Name **und** die Tag-Liste geprüft wird (Match, wenn eines zutrifft).
- Keine Backend-Änderung nötig (`recipe.tags` steht im Context bereits zur Verfügung).
