# Offene Fragen & Anmerkungen zu den User Stories

> **Status: Alle Fragen geklaert** (Stand: 29.03.2026)

## Story 1: Individuelle Personenanzahl pro Rezept

Keine offenen Fragen - die Anforderung ist klar. Technisch straightforward: `custom_servings` Feld auf `MealPlan`.

---

## Story 2: Kompaktere Einkaufsliste + Bemerkungszeile

**Frage: Was genau ist mit "Bemerkungszeile" gemeint?**

**Entscheidung: Pro Zutat (Option A)** - Eine zusaetzliche Spalte "Bemerkung" in der PDF-Tabelle. Eingabe direkt in der Einkaufslisten-Ansicht.

---

## Story 3: Tageweise Rezept-PDF

**Frage: Wie sollen Untergruppen beim Abendessen behandelt werden (Vorspeise/Hauptgang/Salat)?**

**Entscheidung: Neues Feld `sub_category` (Option C)** - Ein optionales Feld auf MealPlan. Untergruppen wie Vorspeise, Hauptgang, Beilage, Salat, Nachtisch werden benoetigt. Das Layout orientiert sich an der bestehenden Excel-Tagesliste (siehe Screenshot): Tagesweise Gliederung mit Menge | Zutat | Zubereitung nebeneinander.

---

## Story 4: Rezept-Vorschau in Wochenuebuersicht

Keine offenen Fragen - Designentscheidung (Modal empfohlen).

---

## Story 5: Reste-Tracker

### Frage 1: Granularitaet - pro Rezept oder pro Zutat?

**Entscheidung: Flexibel, je nach Rezept.** Bei Nachtisch waere pro Zutat unpraktisch (→ pro Rezept erfassen), bei Nudeln mit Sosse ist pro Zutat besser. Der User soll bei jeder Erfassung selbst waehlen koennen.

### Frage 2: Einheit?

**Entscheidung: Prozent oder Freitext.** Keine feste Portionszahl, sondern entweder eine Prozentangabe (z.B. "20% uebrig") oder Freitext (z.B. "3kg Nudeln, 2L Sosse").

### Frage 3: Wann wird eingetragen?

**Entscheidung: Nach jeder Mahlzeit.** Button "Reste erfassen" pro geplanter Mahlzeit im Kalender.

### Frage 4: Was soll die Statistik zeigen?

**Entscheidung: Durchschnittliche Restmenge pro Person, pro Rezept** ueber mehrere Freizeiten hinweg. Beispiel: "Pizzasuppe: In 3 von 5 Freizeiten blieben ca. 15 Portionen uebrig."

### Frage 5: Soll die Statistik automatisch die Skalierung anpassen?

**Entscheidung: Nein, nur als Vorschlag erwaehnen.** Die Statistik zeigt eine Empfehlung an (z.B. "Naechstes Mal fuer 35 statt 45 Personen skalieren"), passt die Skalierung aber nicht automatisch an.

---

## Alle Fragen geklaert

Keine offenen Punkte mehr. Die User Stories in `USER_STORIES.md` werden entsprechend aktualisiert.
