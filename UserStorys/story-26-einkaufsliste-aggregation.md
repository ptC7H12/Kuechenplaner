# Story 26: Einkaufsliste — Massen/Volumen-Einheiten vor Aggregation normalisieren

**Status:** Done
**Aufwand:** Mittel
**Machbarkeit:** Gut
**Implementiert in:** `app/services/unit_converter.py:18-34` (`MASS_TO_BASE`/`VOLUME_TO_BASE`, `normalize_to_base`), `app/services/calculation.py:7-99` (Aggregations-Key auf Basis-Einheit), `app/templates/shopping_list.html:131-156,259-273` (Checkbox-Key `id-unit`, Toast-Display-Name), `tests/test_shopping_list_aggregation.py:80-184` (g/kg-, ml/L-, EL-, Stück-Tests), `tests/test_unit_converter.py:71-89` (`normalize_to_base`-Pure-Tests).

## Beschreibung

Als Küchenplaner möchte ich, dass in der Einkaufsliste (HTML-View **und** PDF-Export) eine Zutat mit denselben Massen- oder Volumen-Einheiten zu einer einzigen Zeile zusammengefasst wird, damit ich beim Einkauf nicht mehrere Posten derselben Zutat zusammenzählen muss.

## Ist-Zustand (mit DB-Diagnose vom 2026-05-18)

Im PDF-Screenshot der Sommerfreizeit 2026:

- Kategorie "Fleisch": `Hackfleisch 1.0 kg` und `Hackfleisch 3.3 kg` als zwei Zeilen — erwartet eine Zeile mit Summe.
- Kategorie "Backwaren": `Mehl 5.3 EL` und `Mehl 36.0 kg` als zwei Zeilen — die kg-Zeile fasst tatsächlich zwei Buckets zusammen (siehe Root-Cause).
- HTML-View zeigt dasselbe Bild — beide Zeilen erscheinen unter "Fleisch", zudem teilen sie sich den Checkbox-State (`shopping_list.html:138-139` verwendet `item.ingredient.name` als Key in `checkedItems`).

**DB-Diagnose** (`%APPDATA%/KuechenApp/app.db`):

- `Hackfleisch` (id=10) wird in 14 Rezepten verwendet: 4× mit `unit='g'` (z. B. Rezept 7 Blätterteig-Gyros 300 g, Rezept 25 Gratin 450 g, Rezept 32 Lagman 500 g), 10× mit `unit='kg'` (z. B. Rezept 22 Hackfleischsoße 4.5 kg, Rezept 61 Spaghetti Bolognese 4.0 kg).
- `Mehl` (id=1) wird in 7 Rezepten verwendet: 1× EL (Rezept 2 Apple crumble 8 EL), 2× g (Rezept 16 Fladenbrot 900 g, Rezept 40 Pancakes 300 g), 4× kg.

Die `UniqueConstraint("name")` schließt aus, dass es zwei `Hackfleisch`- oder `Mehl`-Ingredient-Zeilen mit gleichem Namen gibt — beide haben **eine einzige `ingredient.id`**.

## Root-Cause

Der Aggregations-Schlüssel in `app/services/calculation.py:64` ist `(ingredient.id, unit)`, wobei `unit` aus `RecipeIngredient.unit` stammt (`calculation.py:24`). Wenn dieselbe Zutat in verschiedenen Rezepten mit verschiedenen kompatiblen Einheiten eingetragen ist, entstehen mehrere Buckets:

- Hackfleisch → `(10, 'g')` und `(10, 'kg')`.
- Mehl → `(1, 'EL')`, `(1, 'g')`, `(1, 'kg')`.

`convert_unit()` läuft erst **nach** der Aggregation (`calculation.py:78`) und konvertiert große g-Mengen zu kg. Ergebnis: der `(10, 'g')`-Bucket landet nach Konvertierung als `Hackfleisch X.X kg` — neben dem ohnehin schon existierenden `(10, 'kg')`-Bucket. Zwei Zeilen mit identischer Einheit, die der User als denselben Posten wahrnimmt.

Die ursprüngliche Hypothese "zwei `Ingredient`-Zeilen mit verschiedener Schreibweise" war falsch — die DB-Diagnose hat sie ausgeschlossen.

## Akzeptanzkriterien

- [x] Zutat mit gemischten Masse-Einheiten (g + kg) in verschiedenen Rezepten → eine Zeile in HTML und PDF (Beispiel: Hackfleisch 12.4 kg).
- [x] Zutat mit gemischten Volumen-Einheiten (ml + L) → analog eine Zeile.
- [x] Unterschiedliche Dimensionen (EL vs. kg, Packung vs. g) bleiben getrennte Zeilen (Mehl wäre dann: 1 Zeile "Mehl X kg" + 1 Zeile "Mehl 8 EL").
- [x] HTML-View `shopping_list.html` zeigt dieselbe Aggregation wie der PDF-Export (gleiche Quelle `calculate_shopping_list`).
- [x] Tageslisten-PDF und Excel-Export bleiben konsistent (keine Regression).
- [x] Checkbox-State in `shopping_list.html` nutzt `ingredient.id` + `unit` als Key (statt `ingredient.name`), damit getrennte Zeilen (z.B. "Mehl kg" und "Mehl EL") unabhängige Häkchen haben. Toast-Text zeigt weiterhin den Zutat-Namen.
- [x] Bemerkungen aus `Ingredient.note` mehrerer DB-Duplikate werden in einer aggregierten Zeile mit `; ` zusammengeführt (Duplikate dedupliziert). Camp-spezifische Notizen aus `ShoppingListNote` analog.
- [x] Pytest deckt ab: (a) gemischte g/kg-Einträge → eine Zeile mit korrekt summierter Menge in kg; (b) Mehl mit g/kg/EL → 2 Zeilen (kg + EL); (c) bestehende Single-Unit-Aggregation bleibt korrekt; (d) ml/L → eine Zeile in L.

## Technische Umsetzung

**1. Basis-Einheit-Normalisierung** in `app/services/unit_converter.py`:

`MASS_TO_BASE` / `VOLUME_TO_BASE` als Konstanten ergänzen und eine reine Hilfsfunktion bereitstellen:

```python
MASS_TO_BASE = {'kg': 1000, 'g': 1, 'mg': 0.001}   # Basis: g
VOLUME_TO_BASE = {'L': 1000, 'l': 1000, 'ml': 1}    # Basis: ml

def normalize_to_base(quantity: float, unit: str) -> tuple[float, str]:
    if unit in MASS_TO_BASE:
        return quantity * MASS_TO_BASE[unit], 'g'
    if unit in VOLUME_TO_BASE:
        return quantity * VOLUME_TO_BASE[unit], 'ml'
    return quantity, unit
```

**2. Aggregation** in `app/services/calculation.py:50-100`:

`normalize_to_base` vor dem Aggregations-Key anwenden — der bestehende Casefold-Name-Key bleibt erhalten, sodass `Hackfleisch`/`hackfleisch ` weiterhin kollabieren:

```python
quantity, unit = normalize_to_base(
    ingredient_data['quantity'], ingredient_data['unit']
)
key = ((ingredient.name or '').strip().casefold(),
       (unit or '').strip().casefold())
```

Nach der Aggregation läuft weiterhin `convert_unit()` und macht aus 12400 g → 12,4 kg. Damit:

- `Hackfleisch 300 g + 450 g + 4500 g + 4000 g + ...` → ein Bucket `(hackfleisch, g)` → konvertiert zu kg → **eine Zeile**.
- `Mehl 8 EL` → eigener Bucket `(mehl, el)`; `Mehl 900 g + 1500 g + ...` → ein Bucket `(mehl, g)` → konvertiert zu kg → **zwei Zeilen** (EL + kg).

**3. Notes-Merging:** bereits über `_merge_notes(notes) -> str | None` umgesetzt — joined nicht-leere, distinct Notizen mit `; ` und behält First-Seen-Reihenfolge. Wird auf `global_note` (aus `Ingredient.note` aller im Bucket gesammelten Ingredient-IDs) und `note` (aus `ShoppingListNote` pro Camp+IngredientID) angewendet.

**4. Frontend-Checkbox-Key** in `app/templates/shopping_list.html`:

`item.ingredient.name` als Identifier in `checkedItems` ersetzen durch `'{{ item.ingredient.id }}-{{ item.unit }}'`. Toast-Text und Anzeige verwenden weiterhin `item.ingredient.name`. `toggleItem(key, name)` erhält den Display-Namen als zweites Argument.

**Tests** in `tests/test_shopping_list_aggregation.py`:

- Bestehender Test (`test_duplicate_ingredient_rows_collapse_into_one_line`): Endergebnis prüft `item['quantity']` und `item['unit']` statt `original_quantity` (das ist jetzt in Basis-Einheit g).
- `test_mass_units_collapse_into_one_line`: Hackfleisch 500 g + 2 kg → eine Zeile, 2,5 kg.
- `test_volume_units_collapse_into_one_line`: Saft 800 ml + 1 L → eine Zeile, 1,8 L.
- `test_mehl_g_kg_el_yields_two_lines`: Mehl mit g/kg/EL → genau 2 Zeilen.
- `test_single_unit_aggregation_unchanged`: zwei `Stück`-Einträge bleiben ein Bucket.

## Offene Fragen

- **Stammdaten-Duplikate** in der aktuellen DB: `Hackfleisch` (id=10), `gem. Hackfleisch` (id=223), `Hackfleisch (in soße)` (id=22) sind faktisch dieselbe Zutat unter drei IDs. Analog `Vanilinzucker` (id=35, Tippfehler), `Vanillezucker` (id=145), `Vanillinzucker` (id=29). Diese werden auch nach dem Fix als separate Zeilen erscheinen — gehört in eine eigene Daten-Bereinigungs-Story (Entscheidung 2026-05-18: außerhalb von Story 26).
