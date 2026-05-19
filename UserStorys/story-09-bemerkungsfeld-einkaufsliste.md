# Story 9: Bemerkungs-Feld in Einkaufsliste größer und konsistent

**Status:** Done
**Aufwand:** Klein
**Machbarkeit:** Sehr gut
**Implementiert in:** `app/templates/shopping_list.html:157-164` (`<textarea class="form-textarea">`, Auto-grow via `autoGrowTextarea()`, `@blur` Save, `form-label` konsistent)

## Beschreibung

Als Küchenplaner möchte ich pro Zutat in der Einkaufsliste eine ausreichend große, mehrzeilige Bemerkung erfassen können, und das Feld soll optisch zur restlichen App passen.

## Ist-Zustand

- `app/templates/shopping_list.html:156-163` nutzt `<input type="text">` mit Inline-Tailwind-Klassen (`w-full text-xs px-2 py-1 border border-gray-200 rounded focus:border-blue-400 focus:ring-1 focus:ring-blue-300 focus:outline-none bg-white`)
- Einzeilig, sehr schmal
- Nicht konsistent zu `.form-input`/`.form-textarea` aus `custom.css`, das überall sonst genutzt wird

## Akzeptanzkriterien

- [x] Bemerkungsfeld als `<textarea class="form-textarea" rows="2">` (statt `<input>`)
- [x] Auto-resize bei längeren Texten (Alpine.js)
- [x] Keine Inline-Tailwind-Klassen mehr — ausschließlich `.form-textarea` aus `custom.css`
- [x] Speicher-Trigger: `@blur` mit Debounce (statt nur `onchange`), Endpunkt bleibt `PUT /shopping-list/api/shopping-list/notes/{ingredient_id}`
- [x] Bestehende `window.FreizeitApp.saveShoppingListNote()`-Funktion (`base.html:269-281`) bleibt unverändert

## Technische Umsetzung

- `app/templates/shopping_list.html:156-163`: `<input>` durch `<textarea>` ersetzen
- Auto-resize-Pattern via Alpine.js (`x-data` + `@input` Höhe setzen) — kein neues Lib
- Keine neuen CSS-Regeln nötig
