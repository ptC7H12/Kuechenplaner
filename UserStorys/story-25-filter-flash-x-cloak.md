# Story 25: Rezepte-Seite — Filter-Bereich flackert beim Seitenladen

**Status:** Done
**Aufwand:** Trivial
**Machbarkeit:** Sehr gut
**Implementiert in:** `app/templates/recipes/list.html:148` (`x-cloak` vorhanden), CSS-Regel greift, kein Flackern mehr

## Beschreibung

Als Küchenplaner möchte ich, dass die Rezepte-Seite beim Laden ruhig erscheint — aktuell wird der Filter-Bereich kurz angezeigt und dann vom Alpine-`x-show` ausgeblendet.

## Ist-Zustand

- `app/templates/recipes/list.html:148` `<div x-show="showFilters" x-collapse class="card">` hat kein `x-cloak`
- Standardwert von `showFilters` ist `false` → Bereich soll initial ausgeblendet sein
- Vor JS-Initialisierung ist `x-show` noch nicht aktiv → Browser rendert den Bereich kurz sichtbar → Alpine kickt ein → Bereich verschwindet → Flackern

## Akzeptanzkriterien

- [x] Filter-Bereich ist beim ersten Laden der Seite nicht sichtbar (kein Flackern)
- [x] `x-cloak`-Regel in `base.html` oder `custom.css` ist vorhanden (`[x-cloak] { display: none !important; }`) — falls nicht, ergänzen
- [x] Klick auf "Filter anzeigen" öffnet den Bereich normal
- [x] Keine Regression in anderen Alpine-`x-show`-Bereichen

## Technische Umsetzung

- `app/templates/recipes/list.html:148`: `x-cloak`-Attribut ergänzen → `<div x-show="showFilters" x-collapse x-cloak class="card">`
- Prüfen, ob `[x-cloak]` CSS-Regel in `base.html` oder `custom.css` definiert ist; falls nicht, ergänzen (Standard-Alpine-Pattern)
- Optional: Weitere `x-show`-Bereiche in der Codebase scannen und ggf. `x-cloak` ergänzen
