# Story 3: Tageweise Rezept-PDF (Tages-Kochbuch)

**Status:** Done
**Aufwand:** Mittel
**Machbarkeit:** Gut
**Implementiert in:** `app/models.py` (`MealPlan.sub_category`, Zeile 147), `alembic/versions/005_meal_plan_sub_category.py`, `app/routers/export.py:543` (Endpunkt `GET /export/daily-lists/pdf/{camp_id}`), `tests/test_export_daily_lists.py`, Farbpalette `SUB_CATEGORY_COLORS` (`export.py:34-40`)

## Beschreibung

Als Küchenplaner möchte ich eine PDF exportieren können, in der die Rezepte tageweise gruppiert dargestellt werden (wie die "Tageslisten" in der bisherigen Excel-Planung), damit ich am jeweiligen Tag schnell sehe, was gekocht wird, welche Zutaten ich brauche und wie die Zubereitung geht.

## Ist-Zustand

- **Speiseplan-PDF:** Nur Rezeptnamen in Tabelle (kein Rezeptinhalt)
- **Rezeptbuch-PDF:** Alle Rezepte nacheinander, ohne Tagesbezug
- Es gibt keine Kombination aus beidem
- Der User nutzt bisher eine Excel-Tabelle mit Reiter "Tageslisten" für diesen Zweck

## Referenz-Layout (aus User-Screenshot)

Das gewünschte Format orientiert sich an der bisherigen Excel-Tagesliste:

```
╔══════════════════════════════════════════════════════════╗
║  Samstag, 10.01.2026                                    ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  Frühstück: Creps                                        ║
║  ┌──────────┬──────────────┬─────────────────────────┐   ║
║  │ 1750 g   │ Weizenmehl   │ 1. Mehl, Salz, Eier und │   ║
║  │ 350 g    │ Butter       │    Milch verrühren.      │   ║
║  │ 1400 ml  │ Milch        │ 2. Nach und nach Wasser  │   ║
║  │ 1750 ml  │ Wasser       │    und zerlassene Butter │   ║
║  │ 14       │ Eier         │    zufügen               │   ║
║  │ 7 Prisen │ Salz         │                          │   ║
║  └──────────┴──────────────┴─────────────────────────┘   ║
║                                                          ║
║  Mittag: Pizzasuppe                                      ║
║  ┌──────────┬──────────────┬─────────────────────────┐   ║
║  │ 4,5 kg   │ Hackfleisch  │ 1. Hackfleisch mit      │   ║
║  │ 6,75     │ Zwiebeln     │    Zwiebeln braten.      │   ║
║  │ 9        │ Paprika      │ 2. Paprika würfeln.      │   ║
║  │ ...      │ ...          │ 3. Wasser mit Fleisch-   │   ║
║  │          │              │    brühe anrühren...     │   ║
║  └──────────┴──────────────┴─────────────────────────┘   ║
║                                                          ║
║  Nachtisch: Schneewitchennachtisch                       ║
║  ┌──────────┬────────────────────┬───────────────────┐   ║
║  │ 600 g    │ Zartbitterschoko.. │ 1. Schokolade in  │   ║
║  │ ...      │ ...                │    Stücke teilen.. │   ║
║  └──────────┴────────────────────┴───────────────────┘   ║
║                                                          ║
║  Abendbrot                                               ║
║    Vorspeise: Nachos                                     ║
║    ┌──────────┬──────────────┐                           ║
║    │ 9 Pack.  │ Nachos       │                           ║
║    │ 7 Pack.  │ gerieb. Käse │                           ║
║    │ ...      │ ...          │                           ║
║    └──────────┴──────────────┘                           ║
║    Hauptgang: Kartoffeln mit Hähnchen im Bacon           ║
║    ┌──────────┬──────────────┐                           ║
║    │ 12,31 kg │ Kartoffel    │                           ║
║    │ ...      │ ...          │                           ║
║    └──────────┴──────────────┘                           ║
╚══════════════════════════════════════════════════════════╝
```

**Kernmerkmale aus dem Screenshot:**

- Tagesüberschrift mit Datum + Wochentag
- Mahlzeit-Überschrift mit Rezeptname (z.B. "Frühstück: Creps")
- Zutaten (Menge + Name) und Zubereitung nebeneinander in einer Tabelle
- Mehrere Rezepte pro Mahlzeit möglich (Vorspeise, Hauptgang, Salat beim Abendessen)
- Mengen sind bereits auf Teilnehmerzahl skaliert

## Akzeptanzkriterien

- [x] Neuer Export-Endpunkt: "Tageslisten" PDF
- [x] Gliederung: Tag → Mahlzeit → Rezept(e) mit Zutaten und Zubereitung
- [x] Zutaten und Zubereitungsschritte nebeneinander (3-Spalten-Tabelle: Menge | Zutat | Anleitung)
- [x] Mehrere Rezepte pro Mahlzeit werden untereinander dargestellt
- [x] Mengen sind auf `participant_count` (oder `custom_servings` aus Story 1) skaliert
- [x] Seitenumbruch zwischen Tagen
- [x] Export-Button in der Wochenübersicht verfügbar ("Tageslisten PDF")

## Technische Umsetzung

- Neuer Endpunkt in `export.py`: `GET /export/daily-lists/pdf/{camp_id}`
- Daten: `meal_plans` nach Datum gruppieren, dann nach MealType sortieren
- Pro Rezept eine Tabelle mit 3 Spalten: Menge+Einheit | Zutatname | Zubereitungsschritte
  - Zubereitungsschritte aus `recipe.instructions` parsen (zeilenweise nummeriert)
  - Schritte auf die Tabellenzeilen verteilen (Schritt 1 in Zeile 1, Schritt 2 in Zeile 2, etc.)
- Falls ein Rezept keine Zubereitung hat: 2-Spalten-Tabelle (nur Menge | Zutat)
- Export-Button in `meal_planning/index.html` hinzufügen

## Sub-Kategorien (Vorspeise/Hauptgang/Salat)

**Entscheidung:** Neues optionales Feld `sub_category` auf MealPlan. Mögliche Werte: Vorspeise, Hauptgang, Beilage, Salat, Nachtisch (oder leer). Braucht DB-Migration und UI-Anpassung (Dropdown beim Zuweisen eines Rezepts zum Abendessen).
