; ==============================================================================
; Inno Setup 6 - Freizeit Rezepturverwaltung
; Wird automatisch von build.bat standalone gebaut, sofern Inno Setup 6
; installiert ist (https://jrsoftware.org/isinfo.php).
;
; WICHTIG: AppId darf sich NIEMALS ändern - er identifiziert die App
;          eindeutig bei Windows-Updates und im Deinstallations-Dialog.
; ==============================================================================

#define AppName    "Freizeit Rezepturverwaltung"
; AppVersion kann per Kommandozeile übergeben werden: iscc /DAppVersion=1.2.3 installer.iss
; Fallback: ISPP liest version.txt (FileRead/FileOpen - ReadFile existiert nicht in ISPP)
#ifndef AppVersion
  #define AppVersion Trim(FileRead(FileOpen("version.txt")))
#endif
; AppExe und NameSuffix können für den Debug-Installer überschrieben werden:
;   iscc /DAppExe=FreizeitRezepturverwaltung-debug.exe /DNameSuffix=-debug installer.iss
#ifndef AppExe
  #define AppExe "KuechenApp.exe"
#endif
#ifndef NameSuffix
  #define NameSuffix ""
#endif
#define AppId      "{{D27C6B10-7A89-4768-BB9F-D5123DB65703}"

[Setup]
AppId={#AppId}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=Freizeit Rezepturverwaltung

; Installationspfad - automatisch 64-Bit Program Files
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes

; Ausgabe
OutputDir=installer
OutputBaseFilename=FreizeitRezepturverwaltung-Setup-{#AppVersion}{#NameSuffix}
SetupIconFile=app\static\icon.ico

; Kompression
Compression=lzma2/ultra64
SolidCompression=yes

; Erscheinungsbild
WizardStyle=modern

; 64-Bit-Architektur erzwingen
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

; Deinstallations-Symbol
UninstallDisplayIcon={app}\_internal\{#AppExe}

; Mindestanforderungen
MinVersion=10.0

[Languages]
Name: "german";  MessagesFile: "compiler:Languages\German.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
; Desktop-Verknüpfung standardmäßig angehakt
Name: desktopicon; Description: "Desktop-Verknüpfung erstellen"; Flags: checkedonce

[Files]
; Alle App-Dateien (exe + pyd/dll-Module) - werden bei Updates immer überschrieben.
; Nutzerdaten (Datenbank) liegen in %APPDATA%\KuechenApp\ und werden hier
; bewusst NICHT berührt.
Source: "dist\_internal\*"; DestDir: "{app}\_internal"; \
    Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Startmenü
Name: "{group}\{#AppName}";     Filename: "{app}\_internal\{#AppExe}"; \
    WorkingDir: "{app}\_internal"
Name: "{group}\Deinstallieren"; Filename: "{uninstallexe}"

; Desktop (nur wenn Aufgabe gewählt)
Name: "{commondesktop}\{#AppName}"; Filename: "{app}\_internal\{#AppExe}"; \
    WorkingDir: "{app}\_internal"; Tasks: desktopicon

[Run]
; Optionaler Start nach der Installation
Filename: "{app}\_internal\{#AppExe}"; \
    Description: "{#AppName} jetzt starten"; \
    Flags: nowait postinstall skipifsilent

; ==============================================================================
; HINWEIS ZUM UPDATE-VERHALTEN
; ------------------------------------------------------------------------------
; - App-Dateien in {app}\_internal\ werden bei jedem Update überschrieben.
; - Die Datenbank in %APPDATA%\KuechenApp\app.db wird weder beim Update
;   noch beim Deinstallieren angefasst. Nutzerdaten bleiben immer erhalten.
; - Beim Deinstallieren wird NUR der {app}-Ordner entfernt.
; ==============================================================================
