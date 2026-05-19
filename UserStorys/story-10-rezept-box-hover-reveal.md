# Story 10: Rezept-Box im Speiseplan entlasten (Hover-Reveal)

**Status:** Done
**Aufwand:** Klein-Mittel
**Machbarkeit:** Sehr gut
**Implementiert in:** `app/templates/meal_planning/index.html:174,193` (`.group` & `group-hover:opacity-100` Pattern für Action-Container, Badges bleiben sichtbar)

## Beschreibung

Als Küchenplaner möchte ich im Speiseplan den Rezeptnamen klar lesen können — Action-Buttons sollen sich nicht in den Vordergrund drängen, sondern bei Bedarf erscheinen.

## Ist-Zustand

- `app/templates/meal_planning/index.html:172-233` rendert pro Rezept eine schmale Box (~120px breit) mit:
  - Trash-Button (Löschen)
  - Rezeptname (truncated)
  - Person-Icon (Servings anpassen)
  - Reste-Icon (Reste erfassen)
  - Badges für Custom-Servings und Sub-Category
- Resultat: Name wird abgeschnitten, Box wirkt überladen, siehe Screenshot des Users

## Akzeptanzkriterien

- [x] Im Ruhezustand zeigt die Box nur den Rezeptnamen (volle Breite, möglichst nicht truncated) + Indikator-Badges (Custom-Servings, Sub-Category, Reste-erfasst)
- [x] Action-Icons (Trash, Servings, Reste) erscheinen erst beim Hover via Tailwind `group-hover:opacity-100 opacity-0 transition`
- [x] Mobile: Tap auf die Box toggelt entweder die Action-Leiste oder öffnet das Preview-Modal aus Story 4 mit Aktionen
- [x] Bestehendes Klick-Verhalten (`openPreview`) bleibt erhalten
- [x] Keine neuen CSS-Regeln nötig — Tailwind `group`/`group-hover` reicht aus

## Technische Umsetzung

- `.recipe-card-planned` als `group` markieren
- Action-Container (`<div class="flex">` mit den 3 Buttons) mit `opacity-0 group-hover:opacity-100 transition-opacity`
- Rezeptname `<h4>` darf jetzt `flex-1` einnehmen, weil Buttons in der Nicht-Hover-Phase keinen Platz brauchen
- Mobile-Fallback: optional `@click="actionsVisible = !actionsVisible"` (Alpine.js)
