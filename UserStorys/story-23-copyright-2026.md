# Story 23: Camp-Auswahl — Copyright von 2024 auf 2026

**Status:** Done
**Aufwand:** Trivial
**Machbarkeit:** Sehr gut
**Implementiert in:** `app/templates/camp_select.html` — nur noch Placeholder "z.B. Sommerfreizeit 2024" (Zeile 182) übrig, keine hartkodierten Jahres-Werte in Footern mehr

## Beschreibung

Als Küchenplaner möchte ich, dass das Copyright-Jahr im Footer der Camp-Auswahl aktuell ist.

## Ist-Zustand

- `app/templates/camp_select.html:245` zeigt: `© 2024 Freizeit Rezepturverwaltung`

## Akzeptanzkriterien

- [x] Footer zeigt `© 2026 Freizeit Rezepturverwaltung` (oder dynamisch via `{{ current_year }}`)
- [x] Prüfung, ob noch weitere Templates das Jahr 2024 hartkodiert haben

## Technische Umsetzung

- Variante A (statisch): String in `camp_select.html:245` auf `2026` ändern
- Variante B (dynamisch, empfohlen): Im Render-Context der Startseite `current_year = datetime.now().year` mitgeben und im Template `© {{ current_year }} …`
- Komplette Codebase prüfen: `grep -r "2024" app/templates/`
