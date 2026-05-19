# Story 4: Rezept-Vorschau in der Wochenübersicht

**Status:** Done
**Aufwand:** Klein-Mittel
**Machbarkeit:** Sehr gut
**Implementiert in:** `app/routers/recipes.py:141` (Endpunkt `GET /recipes/{id}/preview`), `app/templates/recipes/preview_modal.html`, `tests/test_recipe_preview.py`, Skalierung integriert

## Beschreibung

Als Küchenplaner möchte ich in der Wochenübersicht mit einem Klick auf ein geplantes Rezept einen schnellen Einblick in das Rezept bekommen, ohne die Seite verlassen zu müssen.

## Ist-Zustand

- In der Wochenübersicht steht nur der Rezeptname (truncated)
- Einzige Interaktion: Löschen-Button
- Für Details muss man zur Rezeptseite navigieren (`/recipes/{id}`)

## Akzeptanzkriterien

- [x] Klick auf ein Rezept in der Wochenübersicht öffnet eine Vorschau
- [x] Vorschau zeigt: Rezeptname, Beschreibung, Zutaten (skaliert), Zubereitungszeit
- [x] Vorschau ist schnell schließbar (Klick außerhalb, X-Button, Escape)
- [x] Optional: Link zur vollständigen Rezeptseite in der Vorschau
- [x] Funktioniert auf Desktop (Mobile ist nice-to-have)

## Technische Umsetzung

- **Option A: Modal/Dialog** (empfohlen)
  - Alpine.js Modal-Komponente in `meal_planning/index.html`
  - HTMX-Request: `GET /recipes/{id}/preview` → liefert HTML-Fragment
  - Neuer Template-Partial: `templates/recipes/preview_modal.html`
  - Neuer Endpunkt in `recipes.py`: Lightweight-Rezeptdaten für Vorschau

- **Option B: Popover/Tooltip**
  - Erscheint bei Hover/Klick direkt neben dem Rezept
  - Kompakter, aber weniger Platz für Infos

## Hinweis

- Modal ist besser geeignet, da genug Platz für Zutaten + Anleitung
- HTMX macht das Laden des Inhalts einfach (`hx-get`, `hx-target`)
