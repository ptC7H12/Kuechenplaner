# Build-Anleitung - Freizeit Rezepturverwaltung

Diese Anleitung beschreibt, wie Sie die Anwendung als eigenständige Desktop-Anwendung kompilieren.

## Voraussetzungen

### 1. Python-Abhängigkeiten installieren

```bash
# Hauptabhängigkeiten
pip install -r requirements.txt

# Build-Abhängigkeiten
pip install -r requirements-build.txt
```

### 2. C-Compiler installieren

Nuitka benötigt einen C-Compiler:

**Windows:**
- **Option A (empfohlen):** Visual Studio Build Tools
  - Download: https://visualstudio.microsoft.com/downloads/
  - Installieren Sie "Build Tools für Visual Studio"
  - Wählen Sie "Desktop-Entwicklung mit C++"

- **Option B:** MinGW64
  - Download: https://www.mingw-w64.org/
  - Fügen Sie MinGW64/bin zum PATH hinzu

**Linux (Debian/Ubuntu):**
```bash
sudo apt-get update
sudo apt-get install gcc g++ python3-dev
```

**macOS:**
```bash
xcode-select --install
```

## Build-Modi

Die Anwendung kann in verschiedenen Modi kompiliert werden:

### Windows Standalone (Schnellste Option für Windows)
**NEU:** Erstellt ein ZIP-Archiv mit embedded Python - KEINE Kompilierung erforderlich!

**Vorteile:**
- ✅ Sehr schneller Build (Minuten statt Stunden)
- ✅ Keine C-Compiler Installation nötig
- ✅ Perfekt für schnelles Testen
- ✅ Vollständig portable

**Windows:**
```bash
python build_windows_standalone.py
```

Das Skript:
1. Lädt embedded Python herunter (~25 MB)
2. Installiert alle Dependencies
3. Erstellt ein ZIP-Archiv im `releases/` Ordner

**Ausgabe:** `releases/Kuechenplaner-1.0.0-windows-standalone-YYYYMMDD.zip`

Benutzer müssen nur das ZIP entpacken und `start.bat` ausführen!

### Nuitka Standalone (Kompiliert)
Erstellt eine einzelne ausführbare Datei mit allen Abhängigkeiten (dauert länger).

**Windows:**
```bash
build.bat standalone
# oder einfach:
python build.py
```

**Linux/macOS:**
```bash
chmod +x build.sh
./build.sh standalone
# oder einfach:
python3 build.py
```

### Fast Mode
Schnellerer Start, aber mehrere Dateien statt einer einzelnen Datei.

**Windows:**
```bash
build.bat fast
```

**Linux/macOS:**
```bash
./build.sh fast
```

### Debug Mode
Mit Debug-Symbolen für Fehleranalyse.

**Windows:**
```bash
build.bat debug
```

**Linux/macOS:**
```bash
./build.sh debug
```

## Build-Ausgabe

Nach erfolgreichem Build finden Sie die kompilierte Anwendung in:

```
dist/
├── FreizeitRezepturverwaltung(.exe)  # Hauptprogramm
└── ... (weitere Dateien bei fast mode)
```

## Ausführen der kompilierten Anwendung

**Windows:**
```bash
dist\FreizeitRezepturverwaltung.exe
```

**Linux:**
```bash
./dist/FreizeitRezepturverwaltung
```

**macOS:**
```bash
open dist/FreizeitRezepturverwaltung.app
```

## Fehlerbehebung

### "Nuitka not found"
```bash
pip install nuitka
```

### "No C compiler found"
Siehe Abschnitt "C-Compiler installieren" oben.

### Build dauert sehr lange
Der erste Build kann 10-30 Minuten dauern. Spätere Builds sind schneller durch Caching.

### "Permission denied" (Linux/macOS)
```bash
chmod +x build.sh
chmod +x dist/FreizeitRezepturverwaltung
```

### Windows Defender blockiert die Exe
Dies ist normal bei selbst-kompilierten Programmen. Fügen Sie eine Ausnahme hinzu:
1. Windows-Sicherheit → Viren- & Bedrohungsschutz
2. Einstellungen verwalten
3. Ausschlüsse hinzufügen
4. Ordner ausschließen → Wählen Sie den `dist` Ordner

## Build-Optimierungen

### Kleinere Dateigrößen

Bearbeiten Sie `build.py` und fügen Sie hinzu:
```python
"--remove-output",  # Entfernt temporäre Build-Dateien
"--no-pyi-file",    # Keine Type-Hint Dateien
```

### Schnellere Builds (Entwicklung)

```bash
# Ohne onefile für schnellere Iterationen
./build.sh fast
```

## Verteilung

Die kompilierte Anwendung kann direkt an Endnutzer verteilt werden:

1. Komprimieren Sie den `dist` Ordner zu einer ZIP-Datei
2. Bei "onefile" Build: Nur die .exe/.app Datei ist nötig
3. Bei "fast" Build: Gesamter dist-Ordner nötig

## Technische Details

### Was wird kompiliert?
- Python-Code → C-Code → Nativer Maschinencode
- Alle Python-Abhängigkeiten werden eingebettet
- Templates und statische Dateien werden als Daten eingebettet

### Datenbankpfad
Die SQLite-Datenbank wird beim ersten Start automatisch erstellt:
- **Windows:** `%APPDATA%/FreizeitRezepturverwaltung/data/`
- **Linux:** `~/.local/share/FreizeitRezepturverwaltung/data/`
- **macOS:** `~/Library/Application Support/FreizeitRezepturverwaltung/data/`

### Logging
Log-Dateien befinden sich im gleichen Verzeichnis wie die Datenbank.

## Support

Bei Problemen:
1. Prüfen Sie die Nuitka-Logs im `build` Ordner
2. Führen Sie den Debug-Build aus
3. Prüfen Sie die Systemanforderungen
