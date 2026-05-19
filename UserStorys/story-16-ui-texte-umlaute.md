# Story 16: UI-Texte konsequent mit Umlauten (statt ae/oe/ue)

**Status:** Done
**Aufwand:** Klein
**Machbarkeit:** Sehr gut
**Implementiert in:** `app/templates/leftovers/*.html`, `app/templates/meal_planning/servings_modal.html`, `app/templates/meal_planning/sub_category_modal.html`, `app/templates/meal_planning/index.html`, `app/templates/recipes/detail.html:211,244` (HTML-Kommentare "Eintraege" → "Einträge")

## Beschreibung

Als Küchenplaner möchte ich, dass alle UI-Texte konsequent deutsche Umlaute (ä/ö/ü/ß) nutzen, damit die Oberfläche professionell wirkt und konsistent zur Mehrheit der Templates ist.

## Ist-Zustand

- Alte Templates (`meal_planning/index.html`, `recipes/list.html`, `shopping_list.html`) nutzen durchgängig Umlaute (z.B. "Frühstück", "Möchten Sie", "Verfügbar")
- Neuere Templates (`leftovers/index.html`, `leftovers/statistics.html`, `leftovers/new_modal.html`, `meal_planning/servings_modal.html`, `meal_planning/sub_category_modal.html`) sowie einige nachträglich eingebaute Strings (`meal_planning/index.html:230`, `recipes/detail.html:208/236`) nutzen ASCII-Ersatz "ae/oe/ue/ss"
- Ergebnis: inkonsistentes Schriftbild

## Akzeptanzkriterien

- [x] In `app/templates/leftovers/*.html` werden alle "fuer", "ueber", "Loeschen", "uebrig", "Naechst...", "moeglich", "Eintraege", "Zurueck" durch die jeweiligen Umlaut-Varianten ersetzt
- [x] In `app/templates/meal_planning/servings_modal.html`, `sub_category_modal.html`, `index.html:230` analog
- [x] In `app/templates/recipes/detail.html:208,236` analog — "Eintraege" in den HTML-Kommentaren `:211,244` zu "Einträge" korrigiert
- [x] Nicht-User-sichtbare Code-Kommentare und Backend-Strings (Logs, Exceptions) bleiben unverändert
- [x] Prüfung: `grep -i "fuer\|ueber\|moeglich\|naechst\|loesch\|uebrig" app/templates/` liefert keine Treffer in sichtbarem Text (verbleibende Hits in `components/forms.html` und `recipes/_form.html` sind Jinja-Kommentare `{# ... #}`)

## Technische Umsetzung

- Reine String-Ersetzungen in Templates, kein Backend-Touch
- Wortliste systematisch durchgehen: `fuer→für`, `ueber→über`, `Uebersicht→Übersicht`, `loeschen/Loeschen→löschen/Löschen`, `uebrig→übrig`, `moeglich→möglich`, `Naechstes→Nächstes`, `Eintraege→Einträge`, `Zurueck→Zurück`, `Reste-Eintraege→Reste-Einträge`
- Achtung bei `&Oslash;` (`leftovers/statistics.html:37`) — die HTML-Entität ist bewusst gewählt, kann bleiben oder zu `Ø` werden
