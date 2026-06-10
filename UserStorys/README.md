# User Storys — Übersicht

Pflegezentrale für alle Feature-Storys des Küchenplaners. Quelle der Wahrheit für Scope und Status. Detailbeschreibung pro Story in der jeweils verlinkten Datei.

## Status-Legende

- **Offen** — noch nicht begonnen
- **In Arbeit** — Implementierung läuft, ggf. Detail-Restpunkte in Story-Dokument oder Sektion "Offene Punkte"
- **Review** — Implementierung abgeschlossen, **manuelle Abnahme durch den User ausstehend** (siehe "Wartet auf mich")
- **Blockiert** — Implementierung pausiert, Klärung durch den User nötig (siehe "Wartet auf mich")
- **Done** — vollständig implementiert und abgenommen (Code + Tests, falls relevant)

Statuswechsel werden durch die Skills `userstory` (anlegen), `story-implement` (bearbeiten, blockieren, in Review stellen) und `story-done` (abnehmen) gesetzt — manuelle Edits sind möglich, sollten aber Tabelle, Counter und Sektionen konsistent halten.

## Storys

| #  | Story                                                                                          | Aufwand        | Status          |
|----|------------------------------------------------------------------------------------------------|----------------|-----------------|
| 1  | [Individuelle Personenanzahl pro Rezept](story-01-individuelle-personenanzahl.md)              | Mittel         | Done            |
| 2  | [Kompaktere Einkaufsliste-PDF + Bemerkung](story-02-kompaktere-einkaufsliste.md)               | Klein          | Done            |
| 3  | [Tageweise Rezept-PDF (Tages-Kochbuch)](story-03-tageweise-rezept-pdf.md)                      | Mittel         | Done            |
| 4  | [Rezept-Vorschau in der Wochenübersicht](story-04-rezept-vorschau.md)                          | Klein-Mittel   | Done            |
| 5  | [Reste-Tracker mit Statistik](story-05-reste-tracker.md)                                       | Groß           | Done            |
| 6  | [Reste-Seite UI angleichen](story-06-reste-seite-ui-angleichen.md)                             | Klein          | Done            |
| 7  | [Reste-Erfassen aktualisieren statt duplizieren](story-07-reste-erfassen-upsert.md)            | Klein-Mittel   | Done            |
| 8  | [Reste-Statistik auf Rezept-Detailseite](story-08-reste-statistik-rezept-detail.md)            | Klein-Mittel   | Done            |
| 9  | [Bemerkungs-Feld Einkaufsliste größer](story-09-bemerkungsfeld-einkaufsliste.md)               | Klein          | Done            |
| 10 | [Rezept-Box im Speiseplan entlasten (Hover)](story-10-rezept-box-hover-reveal.md)              | Klein-Mittel   | Done            |
| 11 | [+Gang Button bei allen Mahlzeiten](story-11-gang-bei-allen-mahlzeiten.md)                     | Sehr klein     | Done            |
| 12 | [Schöne Popups für Personenanzahl und Gang](story-12-popups-personenanzahl-gang.md)            | Klein          | Done            |
| 13 | [Zubereitung in Tagesliste als Textblock](story-13-zubereitung-als-textblock.md)               | Sehr klein     | Done            |
| 14 | [Einheiten-Umrechnung in Rezeptbuch- und Tagesliste-PDF](story-14-einheiten-umrechnung-pdf.md) | Sehr klein     | Done            |
| 15 | [Verfügbare Rezepte alphabetisch A-Z](story-15-rezepte-sortierung-a-z.md)                      | Sehr klein     | Done            |
| 16 | [UI-Texte konsequent mit Umlauten](story-16-ui-texte-umlaute.md)                               | Klein          | Done            |
| 17 | [Reste-Seite Header reduzieren](story-17-reste-seite-header-reduzieren.md)                     | Sehr klein     | Done            |
| 18 | [Reste-Seite — Statistik-Button als FAB](story-18-statistik-button-fab.md)                     | Sehr klein     | Done            |
| 19 | [Reste-Seite Löschen-Button-Bug beheben](story-19-reste-loeschen-bug.md)                       | Sehr klein     | Done            |
| 20 | [Tageslisten-PDF Gänge hierarchisch farbig](story-20-tageslisten-gang-hierarchie.md)           | Klein-Mittel   | Done            |
| 21 | [Speiseplan Hover-Buttons überlappen Badges](story-21-hover-buttons-overlap.md)                | Klein          | Done            |
| 22 | [Speiseplan-PDF Gang und Custom-Servings](story-22-speiseplan-pdf-gang-servings.md)            | Sehr klein     | Done            |
| 23 | [Camp-Auswahl Copyright auf 2026](story-23-copyright-2026.md)                                  | Trivial        | Done            |
| 24 | [Einstellungen Reiter "Infos"](story-24-settings-infos-tab.md)                                 | Klein          | Done            |
| 25 | [Rezepte-Seite Filter-Flackern beheben](story-25-filter-flash-x-cloak.md)                      | Trivial        | Done            |
| 26 | [Einkaufsliste — Masse/Volumen vor Aggregation normalisieren](story-26-einkaufsliste-aggregation.md) | Mittel         | Done            |
| 27 | [Backup-Download Feedback, Uhrzeit & Pfad-Anzeige](story-27-backup-download-feedback.md)       | Klein-Mittel   | Done            |
| 28 | [Backup wiederherstellen & Datenbank zurücksetzen](story-28-backup-restore-reset.md)           | Mittel         | Done            |
| 29 | [Versionsanzeige im Nuitka-Build/Installer reparieren](story-29-version-im-nuitka-build-installer.md) | Klein          | **Review**      |
| 30 | [Zutatenkategorien manuell verwalten](story-30-zutatenkategorien-manuell.md)                   | Mittel         | Done            |
| 31 | [Benutzerdefinierte Einheiten-Konvertierungen speichern und löschen](story-31-benutzerdefinierte-einheiten-konvertierungen.md) | Klein          | Done            |
| 32 | [Update-Hinweis bei neuer Version (GitHub-Release-Check)](story-32-update-hinweis-bei-neuer-version.md) | Klein-Mittel   | **Review**      |
| 33 | [Allergene in den Einstellungen verwalten](story-33-allergene-in-einstellungen-verwalten.md)   | Klein-Mittel   | Done            |
| 34 | [Rezeptliste — Name + Tags/Allergene zweizeilig (auch mobil)](story-34-rezeptliste-name-tags-allergene-zweizeilig.md) | Klein          | Done            |
| 35 | [Allergene strukturiert im Rezeptformular auswählen](story-35-allergene-strukturiert-im-rezeptformular.md) | Klein-Mittel   | Done            |
| 36 | [Speiseplan-Livesearch schließt Tags ein](story-36-speiseplan-livesearch-tags.md)              | Sehr klein     | Done            |
| 37 | [Speiseplan-Tabelle getrennt scrollbar](story-37-speiseplan-tabelle-getrennt-scrollbar.md)     | Sehr klein     | Done            |
| 38 | [Tags/Allergene in Tagesliste- und Rezeptbuch-Export](story-38-tags-allergene-in-export-tagesliste-rezeptbuch.md) | Klein          | Done            |
| 39 | [Zutaten-Kategorie im Rezeptformular bearbeiten](story-39-zutaten-kategorie-im-rezeptformular-bearbeiten.md) | Mittel         | Done            |
## Wartet auf mich

### Review (manuelle Abnahme ausstehend)
- **Story 32** — [Update-Hinweis bei neuer Version (GitHub-Release-Check)](story-32-update-hinweis-bei-neuer-version.md) — App starten und unter Einstellungen → Info kurz prüfen, dass kein Fehler auftritt; optional `version.txt` testweise auf eine niedrigere Version setzen und neu laden → persistenter „Neue Version …"-Toast erscheint, lässt sich nur per × schließen und kommt nach dem Schließen für dieselbe Version nicht wieder (localStorage). Offline-Fall: kein Fehler-Toast.
- **Story 29** — [Versionsanzeige im Nuitka-Build/Installer reparieren](story-29-version-im-nuitka-build-installer.md) — Nach `build.bat standalone` + Installer einmal die Einstellungen → Info aufrufen und prüfen, dass die echte Version (statt "unknown") angezeigt wird; gleiches für `build.bat debug` und `run_build_standalone.bat`.

## Status auf einen Blick

**Done:** 37 · **In Arbeit:** 0 · **Review:** 2 · **Blockiert:** 0 · **Offen:** 0
