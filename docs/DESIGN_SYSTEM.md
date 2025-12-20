# Freizeit Rezepturverwaltung - Design System

## Übersicht

Dieses Design System basiert auf **Material Design 3** Prinzipien und sorgt für ein einheitliches Look & Feel in der gesamten Anwendung.

---

## 🎨 Farbpalette

### Primärfarben

| Farbe | Verwendung | Tailwind-Klasse | Hex-Code |
|-------|-----------|----------------|----------|
| **Indigo** | Primäre Aktionen, Hauptbuttons | `indigo-600` | `#4F46E5` |
| **Purple** | Akzente, Tags, Checkboxen | `purple-600` | `#9333EA` |
| **Teal** | Sekundäre Aktionen, Export-Buttons | `teal-600` | `#0D9488` |
| **Blue** | Informationen, Links (Accent) | `blue-600` | `#2563EB` |

### Statusfarben

| Farbe | Verwendung | Tailwind-Klasse | Hex-Code |
|-------|-----------|----------------|----------|
| **Green** | Erfolg, Erstellen-Aktionen | `green-600` | `#16A34A` |
| **Red** | Fehler, Löschen-Aktionen | `red-600` | `#DC2626` |
| **Amber** | Warnungen | `amber-600` | `#D97706` |
| **Gray** | Neutrale Aktionen, Abbrechen | `gray-600` | `#4B5563` |

### Gradients für Stat-Cards

```css
/* Indigo */
from-indigo-50 to-indigo-100

/* Purple */
from-purple-50 to-purple-100

/* Emerald */
from-emerald-50 to-emerald-100

/* Amber */
from-amber-50 to-amber-100

/* Teal */
from-teal-50 to-teal-100

/* Orange */
from-orange-50 to-orange-100
```

---

## 🔘 Buttons

### Standard Button-Klassen

Verwende **IMMER** die vordefinierten Button-Klassen. **Keine** Inline-Tailwind-Klassen!

```html
<!-- ✅ RICHTIG -->
<button class="btn btn-primary">Speichern</button>
<button class="btn btn-secondary">Abbrechen</button>
<button class="btn btn-danger">Löschen</button>

<!-- ❌ FALSCH -->
<button class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md">
  Speichern
</button>
```

### Verfügbare Button-Varianten

| Klasse | Verwendung | Farbe |
|--------|-----------|-------|
| `.btn-primary` | Hauptaktionen (Speichern, Öffnen) | Indigo |
| `.btn-secondary` | Sekundäraktionen (Abbrechen, Zurück) | Gray |
| `.btn-success` | Erstellen-Aktionen | Green |
| `.btn-danger` | Lösch-Aktionen | Red |
| `.btn-accent` | Besondere Aktionen (Schnellstart) | Blue |

### Button-Größen & Modifikatoren

```html
<!-- Volle Breite -->
<button class="btn btn-primary w-full">Vollbreiter Button</button>

<!-- Disabled State -->
<button class="btn btn-primary" disabled>Deaktiviert</button>

<!-- Mit Icon -->
<button class="btn btn-primary">
  <svg class="w-5 h-5 mr-2">...</svg>
  Button mit Icon
</button>
```

### Button-Styling Details

```css
/* Definiert in custom.css */
.btn {
  @apply inline-flex items-center justify-center
         px-5 py-2.5 text-sm font-semibold rounded-xl
         shadow-md hover:shadow-lg
         transition-all duration-200
         focus:outline-none focus:ring-4 focus:ring-offset-2;
}

.btn-primary {
  @apply bg-indigo-600 text-white
         hover:bg-indigo-700 hover:scale-105
         focus:ring-indigo-300;
}
```

---

## 📝 Formulare

### Form Input-Klassen

Verwende **IMMER** `.form-*` Klassen für Formularelemete.

```html
<!-- ✅ RICHTIG -->
<label for="name" class="form-label">Name *</label>
<input type="text" id="name" class="form-input" placeholder="...">

<select class="form-select">...</select>
<textarea class="form-textarea"></textarea>

<!-- ❌ FALSCH -->
<label class="block text-sm font-medium text-gray-700">Name</label>
<input class="w-full px-3 py-2 border border-gray-300 rounded-md">
```

### Verfügbare Form-Klassen

| Klasse | Element | Verwendung |
|--------|---------|-----------|
| `.form-label` | `<label>` | Beschriftungen |
| `.form-input` | `<input>` | Text, Date, Number, etc. |
| `.form-select` | `<select>` | Dropdown-Listen |
| `.form-textarea` | `<textarea>` | Mehrzeilige Texteingabe |
| `.form-checkbox` | `<input type="checkbox">` | Checkboxen |
| `.form-radio` | `<input type="radio">` | Radio-Buttons |
| `.form-input-color` | `<input type="color">` | Farbwähler |
| `.form-error` | `<p>` | Fehlermeldungen |
| `.form-help` | `<p>` | Hilfetexte |

### Color Picker (Spezialfall)

```html
<input type="color" class="form-input form-input-color" value="#3B82F6">
<button class="btn btn-primary form-input-color">Hinzufügen</button>
```

**Hinweis:** `.form-input-color` setzt eine feste Höhe (2.875rem) für vertikale Ausrichtung.

---

## 🃏 Cards

### Card-Klassen

```html
<!-- Standard Card -->
<div class="card">
  <h2 class="card-title">Titel</h2>
  <p>Inhalt...</p>
</div>

<!-- Card mit Header -->
<div class="card">
  <div class="card-header">
    <h2 class="card-title">Titel</h2>
    <button>Aktion</button>
  </div>
  <p>Inhalt...</p>
</div>

<!-- Interaktive Card -->
<div class="card-hover" onclick="...">
  <p>Klickbare Card...</p>
</div>
```

### Card-Styling

```css
.card {
  @apply bg-white rounded-2xl shadow-md p-6
         transition-all duration-300 hover:shadow-lg;
}

.card-hover {
  @apply bg-white rounded-2xl shadow-md p-6
         transition-all duration-300 hover:shadow-xl hover:translate-y-[-2px]
         cursor-pointer;
}

.card-header {
  @apply flex items-center justify-between mb-5 pb-4 border-b-2 border-gray-200;
}
```

---

## 📊 Stat Cards

### Verwendung

Stat Cards zeigen Statistiken/Metriken an und verwenden Gradient-Hintergründe.

```html
<!-- Mit Component (statische Daten) -->
{% with
    color="indigo",
    icon='<svg class="w-6 h-6 text-indigo-600">...</svg>',
    value="42",
    label="Rezepte",
    description="Gesamt"
%}
    {% include "components/stat_card.html" %}
{% endwith %}

<!-- Inline (dynamische Daten mit Alpine.js) -->
<div class="bg-gradient-to-br from-indigo-50 to-indigo-100 rounded-lg p-6 hover:shadow-lg transition-all">
    <div class="flex items-start justify-end mb-3">
        <div class="p-2 bg-white rounded-lg shadow-sm">
            <svg class="w-6 h-6 text-indigo-600">...</svg>
        </div>
    </div>
    <div class="text-2xl font-bold text-indigo-900 mb-1" x-text="count"></div>
    <div class="text-sm font-medium text-indigo-700 mb-2">Label</div>
    <div class="text-xs text-indigo-600">Beschreibung</div>
</div>
```

### Wann welche Variante?

- **Component (`stat_card.html`)**: Für statische Werte (Dashboard)
- **Inline**: Für dynamische Werte mit Alpine.js (Rezeptliste mit Filter)

---

## 🚀 Floating Action Buttons (FABs)

FABs sind für primäre Aktionen auf einer Seite. Positioniert **immer** `bottom-6 right-6`.

### FAB-Struktur

```html
<!-- Extended FAB (mit Text) -->
<div class="fixed bottom-6 right-6 flex flex-col gap-3 z-50">
    <!-- Sekundäre Aktion (oben) -->
    <a href="/export/pdf"
       class="flex items-center px-4 py-3 bg-teal-600 text-white rounded-full shadow-2xl hover:bg-teal-700 hover:shadow-xl hover:scale-105 transition-all duration-300 active:scale-95 focus:outline-none focus:ring-4 focus:ring-teal-300"
       title="Als PDF exportieren">
        <svg class="w-5 h-5 mr-2">...</svg>
        <span class="text-sm font-semibold">PDF Export</span>
    </a>

    <!-- Primäre Aktion (unten) -->
    <a href="/create"
       class="flex items-center px-4 py-3 bg-indigo-600 text-white rounded-full shadow-2xl hover:bg-indigo-700 hover:shadow-xl hover:scale-105 transition-all duration-300 active:scale-95 focus:outline-none focus:ring-4 focus:ring-indigo-300"
       title="Neu erstellen">
        <svg class="w-5 h-5 mr-2">...</svg>
        <span class="text-sm font-semibold">Neu erstellen</span>
    </a>
</div>
```

### FAB-Farbschema

| Aktion | Farbe | Verwendung |
|--------|-------|-----------|
| **Primär** | `indigo-600` | Hauptaktion (Erstellen) |
| **Sekundär** | `teal-600` | Export, Download |
| **Erfolg** | `green-600` | (falls benötigt) |

### FAB-Beispiele

```html
<!-- Rezeptliste -->
- Teal: PDF Export (sekundär)
- Indigo: Neues Rezept (primär)

<!-- Mahlzeitenplanung -->
- Teal: PDF Export (sekundär)

<!-- Einkaufsliste -->
- Teal: Excel Export (sekundär)
- Indigo: PDF Export (primär)
```

---

## 🎭 Elevations (Schatten)

Material Design verwendet Schatten für Tiefe und Hierarchie.

### Shadow-System

| Level | Verwendung | Tailwind-Klasse |
|-------|-----------|----------------|
| **1** | Subtile Elevation | `shadow-sm` |
| **2** | Standard Cards, Inputs | `shadow-md` |
| **3** | Hover Cards, Dropdowns | `shadow-lg` |
| **4** | Modals, Hover Buttons | `shadow-xl` |
| **5** | FABs, wichtige Overlays | `shadow-2xl` |

### Interaktive Schatten

```css
/* Cards */
.card {
  shadow-md → hover:shadow-lg
}

/* Buttons */
.btn {
  shadow-md → hover:shadow-lg
}

/* FABs */
.fab {
  shadow-2xl → hover:shadow-xl
}
```

---

## 📐 Border Radius

Konsistente Rundungen für ein harmonisches Design.

### Radius-System

| Element | Radius | Tailwind-Klasse |
|---------|--------|----------------|
| **Buttons** | 12px | `rounded-xl` |
| **Cards** | 16px | `rounded-2xl` |
| **FABs** | ∞ | `rounded-full` |
| **Inputs** | 8px | `rounded-lg` |
| **Badges** | 8px | `rounded-lg` |
| **Small Elements** | 6px | `rounded-md` |

---

## 📱 Responsive Design

### Breakpoints

```css
/* Tailwind Default Breakpoints */
sm:  640px   /* Tablet portrait */
md:  768px   /* Tablet landscape */
lg:  1024px  /* Desktop */
xl:  1280px  /* Large desktop */
2xl: 1536px  /* Extra large */
```

### Responsive Grid

```html
<!-- 1 Spalte mobil, 2 auf Tablet, 4 auf Desktop -->
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
  <!-- Stat Cards -->
</div>
```

---

## ✅ Best Practices

### DO's ✅

1. **Verwende CSS-Klassen** statt Inline-Styles
   ```html
   ✅ <button class="btn btn-primary">OK</button>
   ❌ <button style="background: blue; padding: 10px;">OK</button>
   ```

2. **Konsistente Abstände**
   ```html
   ✅ <div class="space-y-6">...</div>
   ✅ <div class="grid gap-5">...</div>
   ```

3. **Icons mit Text**
   ```html
   ✅ <button class="btn btn-primary">
        <svg class="w-5 h-5 mr-2">...</svg>
        Text
      </button>
   ```

4. **Semantische Klassen**
   ```html
   ✅ <button class="btn btn-danger">Löschen</button>
   ❌ <button class="btn-red">Löschen</button>
   ```

### DON'Ts ❌

1. **Keine Inline-Tailwind für Buttons/Forms**
   ```html
   ❌ <button class="px-4 py-2 bg-blue-600 rounded-md">
   ✅ <button class="btn btn-primary">
   ```

2. **Keine gemischten Border-Radiusse**
   ```html
   ❌ <div class="card rounded-md">  /* Cards = rounded-2xl */
   ✅ <div class="card">
   ```

3. **Keine inkonsistenten Farben**
   ```html
   ❌ <button class="bg-sky-600">  /* Verwende indigo-600 */
   ✅ <button class="btn btn-primary">
   ```

---

## 🎯 Checkliste für neue Features

Vor dem Commit prüfen:

- [ ] Alle Buttons verwenden `.btn-*` Klassen
- [ ] Alle Inputs verwenden `.form-*` Klassen
- [ ] Cards verwenden `rounded-2xl`
- [ ] FABs verwenden `rounded-full` und `shadow-2xl`
- [ ] Farben folgen dem Farbschema (indigo/teal/green/red)
- [ ] Shadows folgen dem Elevation-System
- [ ] Responsive Klassen für Tablet/Desktop
- [ ] Icons sind 20px (w-5 h-5) mit mr-2 Abstand

---

## 📚 Komponenten-Referenz

### Verzeichnis-Struktur

```
app/
├── static/
│   └── css/
│       └── custom.css          # Design System CSS
├── templates/
│   ├── components/
│   │   ├── stat_card.html      # Statistik-Karte
│   │   ├── fab_button.html     # Floating Action Button
│   │   ├── info_card.html      # Info-Karte
│   │   └── edit_camp_modal.html # Modal für Freizeit-Edit
│   └── base.html               # Base Template mit Material Icons
```

### Verwendete Libraries

- **Tailwind CSS 3.x**: Utility-first CSS Framework
- **Material Icons**: Google Material Icons
- **Alpine.js**: Leichtgewichtiges JavaScript Framework
- **HTMX**: Moderne HTML-Interaktivität

---

## 🔄 Migration Guide

### Von alten Inline-Styles zu Design System

#### Buttons

```html
<!-- Alt -->
<button class="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-md">

<!-- Neu -->
<button class="btn btn-primary">
```

#### Inputs

```html
<!-- Alt -->
<input class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2">

<!-- Neu -->
<input class="form-input">
```

#### Cards

```html
<!-- Alt -->
<div class="bg-white shadow-lg rounded-lg p-6">

<!-- Neu -->
<div class="card">
```

---

## 📝 Changelog

### Version 1.0.0 - 2025-12-20

**Initial Release**

- ✅ Standardisierte Button-Klassen (`.btn-*`)
- ✅ Standardisierte Form-Klassen (`.form-*`)
- ✅ Card-System mit `rounded-2xl`
- ✅ FAB-System mit konsistenten Farben
- ✅ Elevation-System (shadow-md bis shadow-2xl)
- ✅ Farbpalette (indigo/purple/teal als Primär)
- ✅ Responsive Grid-System

**Breaking Changes:**

- Buttons benötigen jetzt `.btn btn-*` Klassen
- Inputs benötigen jetzt `.form-*` Klassen
- Cards verwenden `rounded-2xl` statt `rounded-xl`

---

## 🤝 Beiträge

Bei Änderungen am Design System:

1. Update `custom.css` mit neuen Klassen
2. Update diese Dokumentation
3. Update betroffene Templates
4. Teste auf allen Breakpoints (mobil/tablet/desktop)
5. Erstelle aussagekräftigen Git-Commit

**Commit-Konvention:**

```
refactor(design): [Beschreibung]
feat(design): [Neue Design-Feature]
fix(design): [Design-Bugfix]
```

---

**Fragen?** Siehe TECHNICAL_README.md für technische Details.
