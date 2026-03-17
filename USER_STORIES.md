# User Stories - Neue Anforderungen

## Kritische Bewertung & Offene Fragen

Bevor wir loslegen, hier meine Einschätzung und ein paar Rückfragen:

### Offene Fragen

1. **Bemerkungszeile Einkaufsliste (Story 2):** Ist damit eine Bemerkung *pro Zutat* gemeint (z.B. "Bio kaufen", "nur bei Rewe") oder eine allgemeine Bemerkungszeile am Ende der Liste (z.B. "Bitte alles bis Freitag besorgen")?

2. **Tageweise Rezept-PDF (Story 3):** Du sagst, du schickst noch ein Foto. Ohne das Foto vermute ich: Ihr wollt eine PDF, die Tag für Tag auflistet welche Rezepte mit Zutaten und Zubereitung dran sind - quasi ein "Tages-Kochbuch". Stimmt das? Oder reicht der Speiseplan-Export nur mit besserem Layout?

3. **Reste-Tracker (Story 5):** Das ist das größte Feature. Dazu bräuchte ich mehr Details:
   - Was genau wird erfasst? Beispiel: "Nudeln mit Tomatensoße → 3kg Nudeln übrig, 2L Soße übrig" (pro Zutat) oder eher "Nudeln mit Tomatensoße → ca. 15 Portionen übrig" (pro Rezept)?
   - Wann wird das eingetragen? Nach jeder Mahlzeit?
   - Was für eine Statistik? Z.B. "Bei Rezept X bleiben im Schnitt 20% übrig" über mehrere Freizeiten hinweg?
   - Soll die Statistik helfen, beim nächsten Mal weniger einzukaufen (also die Skalierung anpassen)?

---

## Story 1: Individuelle Personenanzahl pro Rezept im Mahlzeitenplan

**Aufwand:** Mittel | **Machbarkeit:** Gut

### Beschreibung
Als Küchenplaner möchte ich für einzelne Rezepte im Mahlzeitenplan eine abweichende Personenanzahl angeben können, damit ich flexibel planen kann, wenn z.B. beim Frühstück weniger Leute essen als beim Mittagessen.

### Ist-Zustand
- `participant_count` liegt auf dem **Camp** (global für alle Mahlzeiten)
- Skalierung: `camp.participant_count / recipe.base_servings`
- Kein Override pro MealPlan-Eintrag möglich

### Akzeptanzkriterien
- [ ] Jeder MealPlan-Eintrag hat ein optionales Feld `custom_servings`
- [ ] Wenn `custom_servings` gesetzt ist, wird dieses statt `camp.participant_count` für die Skalierung verwendet
- [ ] In der Wochenübersicht ist die abweichende Personenanzahl sichtbar (z.B. kleiner Badge)
- [ ] Beim Drag & Drop eines Rezepts kann optional eine Personenanzahl eingegeben werden
- [ ] Die Einkaufsliste berücksichtigt die individuellen Personenanzahlen korrekt
- [ ] Der PDF-Export (Rezeptbuch) zeigt die korrekte Personenanzahl pro Rezept

### Technische Umsetzung
- `MealPlan.custom_servings` (Integer, nullable) in `models.py` hinzufügen
- `calculation.py` → `calculate_shopping_list()` anpassen: `custom_servings or camp.participant_count`
- UI: Kleines Eingabefeld oder Popup beim Platzieren/Bearbeiten eines Rezepts
- Alle Export-Funktionen in `export.py` anpassen

### Hinweise
- Standardverhalten bleibt: Ohne Override gilt weiterhin `camp.participant_count`
- DB-Migration nötig (neues Feld in `meal_plans` Tabelle)

---

## Story 2: Kompaktere Einkaufsliste-PDF + Bemerkungszeile

**Aufwand:** Klein | **Machbarkeit:** Sehr gut

### Beschreibung
Als Küchenplaner möchte ich eine kompaktere Einkaufsliste als PDF exportieren können und eine Möglichkeit haben, Bemerkungen hinzuzufügen, damit die Liste praktischer beim Einkaufen ist.

### Ist-Zustand
- Großzügige Abstände: 2cm Ränder, `Spacer(1, 20)` zwischen Kategorien
- Schriftgrößen: Titel 24pt, Überschriften 16pt
- Keine Möglichkeit für Bemerkungen
- Tabelle: 3 Spalten (Zutat, Menge, Einheit) - relativ breit

### Akzeptanzkriterien
- [ ] PDF-Ränder reduziert (z.B. 1.5cm statt 2cm)
- [ ] Abstände zwischen Kategorien verringert
- [ ] Schriftgrößen etwas kleiner (Titel 18pt, Überschriften 13pt)
- [ ] Tabellenzeilen kompakter (weniger Padding)
- [ ] Bemerkungszeile vorhanden (abhängig von Klärung - siehe offene Fragen)
- [ ] Die Liste passt auf weniger Seiten als vorher

### Technische Umsetzung
- `export.py` → `export_shopping_list_pdf()` anpassen:
  - Margins reduzieren
  - Spacer verkleinern
  - Font-Sizes reduzieren
  - TableStyle: Padding reduzieren
- Für Bemerkungen: Entweder neue Spalte in Tabelle oder Textfeld am Ende

### Varianten für Bemerkungszeile (zu klären)
**Option A:** Zusätzliche Spalte "Bemerkung" in der Tabelle pro Zutat
**Option B:** Freitext-Bereich am Ende der gesamten Liste
**Option C:** Freitext-Bereich pro Kategorie

---

## Story 3: Tageweise Rezept-PDF (Tages-Kochbuch)

**Aufwand:** Mittel | **Machbarkeit:** Gut

### Beschreibung
Als Küchenplaner möchte ich eine PDF exportieren können, in der die Rezepte tageweise gruppiert dargestellt werden, damit ich am jeweiligen Tag schnell sehe, was gekocht wird und welche Zutaten/Anleitungen ich brauche.

### Ist-Zustand
- **Speiseplan-PDF:** Nur Rezeptnamen in Tabelle (kein Rezeptinhalt)
- **Rezeptbuch-PDF:** Alle Rezepte nacheinander, ohne Tagesbezug
- Es gibt keine Kombination aus beidem

### Akzeptanzkriterien
- [ ] Neuer Export-Endpunkt: "Tages-Kochbuch" PDF
- [ ] Gliederung: Tag → Mahlzeit (Frühstück/Mittag/Abend) → Rezept(e) mit Details
- [ ] Pro Rezept: Name, skalierte Zutaten, Zubereitung
- [ ] Seitenumbruch zwischen Tagen (oder zumindest klare visuelle Trennung)
- [ ] Teilnehmeranzahl und Skalierung korrekt angezeigt
- [ ] Export-Button in der Wochenübersicht verfügbar

### Technische Umsetzung
- Neuer Endpunkt in `export.py`: `GET /export/daily-cookbook/pdf/{camp_id}`
- Daten: `meal_plans` nach Datum gruppieren, dann nach MealType sortieren
- Layout pro Tag:
  ```
  === Tag 1: Montag, 15.07.2025 ===

  --- Frühstück ---
  Rezept: Müsli mit Obst (45 Portionen)
  Zutaten: ...
  Zubereitung: ...

  --- Mittagessen ---
  Rezept: Nudeln mit Tomatensoße (45 Portionen)
  ...
  ```
- Export-Button in `meal_planning/index.html` hinzufügen

### Hinweis
- Warte auf das Foto vom User, um das genaue Layout zu klären

---

## Story 4: Rezept-Vorschau in der Wochenübersicht

**Aufwand:** Klein-Mittel | **Machbarkeit:** Sehr gut

### Beschreibung
Als Küchenplaner möchte ich in der Wochenübersicht mit einem Klick auf ein geplantes Rezept einen schnellen Einblick in das Rezept bekommen, ohne die Seite verlassen zu müssen.

### Ist-Zustand
- In der Wochenübersicht steht nur der Rezeptname (truncated)
- Einzige Interaktion: Löschen-Button
- Für Details muss man zur Rezeptseite navigieren (`/recipes/{id}`)

### Akzeptanzkriterien
- [ ] Klick auf ein Rezept in der Wochenübersicht öffnet eine Vorschau
- [ ] Vorschau zeigt: Rezeptname, Beschreibung, Zutaten (skaliert), Zubereitungszeit
- [ ] Vorschau ist schnell schließbar (Klick außerhalb, X-Button, Escape)
- [ ] Optional: Link zur vollständigen Rezeptseite in der Vorschau
- [ ] Funktioniert auf Desktop (Mobile ist nice-to-have)

### Technische Umsetzung
- **Option A: Modal/Dialog** (empfohlen)
  - Alpine.js Modal-Komponente in `meal_planning/index.html`
  - HTMX-Request: `GET /recipes/{id}/preview` → liefert HTML-Fragment
  - Neuer Template-Partial: `templates/recipes/preview_modal.html`
  - Neuer Endpunkt in `recipes.py`: Lightweight-Rezeptdaten für Vorschau

- **Option B: Popover/Tooltip**
  - Erscheint bei Hover/Klick direkt neben dem Rezept
  - Kompakter, aber weniger Platz für Infos

### Hinweis
- Modal ist besser geeignet, da genug Platz für Zutaten + Anleitung
- HTMX macht das Laden des Inhalts einfach (`hx-get`, `hx-target`)

---

## Story 5: Reste-Tracker mit Statistik

**Aufwand:** Groß | **Machbarkeit:** Gut, aber klärungsbedürftig

### Beschreibung
Als Küchenplaner möchte ich nach jeder Mahlzeit erfassen können, was und wie viel übrig geblieben ist, und über mehrere Freizeiten eine Statistik pro Rezept sehen, damit ich beim nächsten Mal besser planen kann.

### Ist-Zustand
- Kein Reste-Tracking in der App
- Wird aktuell manuell (Zettel/Notizen) erfasst

### Akzeptanzkriterien
- [ ] Neuer Navigations-Reiter "Reste" in der Sidebar
- [ ] Erfassung von Resten pro Mahlzeit/Rezept nach der Zubereitung
- [ ] Freitext-Feld für Art der Reste + Mengenangabe
- [ ] Übersicht aller erfassten Reste für das aktuelle Camp
- [ ] Statistik pro Rezept über mehrere Camps hinweg
- [ ] Statistik zeigt z.B. Durchschnitt, Trend, Empfehlung

### Technische Umsetzung (Entwurf - abhängig von Klärung)

**Neues Model:**
```python
class Leftover(Base):
    __tablename__ = 'leftovers'

    id = Column(Integer, primary_key=True)
    meal_plan_id = Column(Integer, ForeignKey('meal_plans.id'))
    recipe_id = Column(Integer, ForeignKey('recipes.id'))
    camp_id = Column(Integer, ForeignKey('camps.id'))
    description = Column(Text)           # "3kg Nudeln, 2L Soße"
    quantity_estimate = Column(Float)     # Geschätzte Portionen übrig
    notes = Column(Text)                 # Freitext
    created_at = Column(DateTime)
```

**Neue Dateien:**
- `app/routers/leftovers.py` - CRUD + Statistik-Endpunkte
- `app/templates/leftovers/index.html` - Übersicht + Erfassung
- `app/templates/leftovers/statistics.html` - Statistik-Ansicht

**Statistik-Ideen:**
- Durchschnittliche Restmenge pro Rezept (über alle Camps)
- "Rezept X: In 3 von 5 Freizeiten blieben ca. 15 Portionen übrig"
- Vorschlag: "Nächstes Mal nur für 35 statt 45 Personen skalieren"

### Offene Punkte (müssen geklärt werden)
1. Granularität: Pro Rezept oder pro Zutat?
2. Einheit: Portionen, kg, Freitext?
3. Zeitpunkt der Erfassung: Nach jeder Mahlzeit oder am Ende des Tages?
4. Soll die Statistik automatisch die Skalierung für nächstes Mal anpassen?

---

## Priorisierungs-Vorschlag

| Prio | Story | Aufwand | Begründung |
|------|-------|---------|------------|
| 1 | Story 2: Kompaktere Einkaufsliste | Klein | Quick Win, sofort spürbar |
| 2 | Story 4: Rezept-Vorschau | Klein-Mittel | Verbessert tägliche Nutzung stark |
| 3 | Story 1: Individuelle Personenanzahl | Mittel | Wichtig für flexible Planung |
| 4 | Story 3: Tageweise Rezept-PDF | Mittel | Wartet auf Foto/Klärung vom User |
| 5 | Story 5: Reste-Tracker | Groß | Braucht noch Klärung, größtes Feature |
