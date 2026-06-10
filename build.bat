@echo off
REM Build script for Freizeit Rezepturverwaltung (Windows)

setlocal enabledelayedexpansion

set BUILD_MODE=%1
if "%BUILD_MODE%"=="" set BUILD_MODE=standalone
set CLEAN_BUILD=%2
set PROJ_DIR=%~dp0
set "NUITKA_VOPT="
if /i "%NUITKA_VERBOSE%"=="1" set "NUITKA_VOPT=--verbose"
if /i "%NUITKA_VERBOSE%"=="true" set "NUITKA_VOPT=--verbose"
if /i "%NUITKA_VERBOSE%"=="yes" set "NUITKA_VOPT=--verbose"
if /i "%NUITKA_VERBOSE%"=="on" set "NUITKA_VOPT=--verbose"

echo ========================================
echo Freizeit Rezepturverwaltung Build
echo ========================================
echo.

REM Python 3.14 wird von pythonnet (pywebview-Abhaengigkeit) und Nuitka nicht unterstuetzt.
REM Verwende explizit Python 3.12 ueber den py-Launcher.
set PYTHON_EXE=py -3.12
%PYTHON_EXE% --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python 3.12 nicht gefunden ^(py -3.12^).
    echo Installieren von https://www.python.org/downloads/release/python-3120/
    exit /b 1
)
echo Python: %PYTHON_EXE%
echo.

REM Check if Nuitka is installed
%PYTHON_EXE% -m nuitka --version >nul 2>&1
if errorlevel 1 (
    echo Error: Nuitka ist fuer %PYTHON_EXE% nicht installiert
    echo Installieren mit: %PYTHON_EXE% -m pip install nuitka
    exit /b 1
)

REM Nuitka legt unter --output-dir=dist u.a. main.build (C-Compile-Cache) und main.dist ab.
REM dist komplett zu loeschen verwirft den inkrementellen Build jedes Mal.
if /i "%CLEAN_BUILD%"=="clean" (
    echo Vollstaendiger Clean: dist, Nuitka-Cache, embed-Python build-Ordner...
    if exist dist rmdir /s /q dist
    if exist build rmdir /s /q build
    if exist "%PROJ_DIR%.nuitka_cache" rmdir /s /q "%PROJ_DIR%.nuitka_cache"
) else (
    echo Inkrementell: behalte dist\main.build und .nuitka_cache ^(Nuitka-Hilfs-Caches^).
    echo Nur alte Ausgabeordner werden entfernt; main.build bleibt fuer schnellere Rebuilds.
    echo Vollstaendiger Rebuild: .\build.bat %BUILD_MODE% clean
    if exist dist\_internal rmdir /s /q dist\_internal
    if exist dist\main.dist rmdir /s /q dist\main.dist
)

echo Build mode: %BUILD_MODE%
echo.

if "%BUILD_MODE%"=="standalone" (
    echo Building standalone executable...
    %PYTHON_EXE% build.py
    if errorlevel 1 exit /b 1
) else if "%BUILD_MODE%"=="debug" (
    echo Building with console enabled for debug output ^(RAM-optimized^)...
    %PYTHON_EXE% -m nuitka ^
        --standalone ^
        --output-dir=dist ^
        --output-filename=FreizeitRezepturverwaltung-debug.exe ^
        --include-data-dir=app/templates=app/templates ^
        --include-data-dir=app/static=static ^
        --include-data-dir=alembic=alembic_migration ^
        --include-data-files=alembic/env.py=alembic_migration/env.py ^
        --include-data-files=alembic/versions/*.py=alembic_migration/versions/ ^
        --include-data-file=alembic.ini=alembic.ini ^
        --include-data-file=version.txt=version.txt ^
        --include-package=app ^
        --include-package=fastapi ^
        --include-package=uvicorn ^
        --include-package=sqlalchemy ^
        --include-package=pydantic ^
        --include-package=webview ^
        --include-package=jinja2 ^
        --include-package=reportlab ^
        --include-package=openpyxl ^
        --include-package=starlette ^
        --include-package=pydantic_core ^
        --nofollow-import-to=webview.platforms.android ^
        --nofollow-import-to=webview.platforms.gtk ^
        --nofollow-import-to=webview.platforms.cocoa ^
        --nofollow-import-to=webview.platforms.qt ^
        --nofollow-import-to=reportlab.lib.testutils ^
        --nofollow-import-to=reportlab.graphics.testshapes ^
        --nofollow-import-to=sqlalchemy.dialects.mysql ^
        --nofollow-import-to=sqlalchemy.dialects.oracle ^
        --nofollow-import-to=sqlalchemy.dialects.mssql ^
        --nofollow-import-to=sqlalchemy.ext.mypy ^
        --nofollow-import-to=dns ^
        --nofollow-import-to=email_validator ^
        --nofollow-import-to=numpy ^
        --nofollow-import-to=pandas ^
        --nofollow-import-to=scipy ^
        --nofollow-import-to=matplotlib ^
        --nofollow-import-to=pytest ^
        --lto=no ^
        --jobs=1 ^
        --verbose ^
        app/main.py
    if errorlevel 1 exit /b 1
    REM Modules in _internal verstecken, Launcher in dist\ ablegen
    if exist dist\_internal rmdir /s /q dist\_internal
    move "dist\main.dist" "dist\_internal" > nul
    powershell -NoProfile -Command "$ws=New-Object -ComObject WScript.Shell; $s=$ws.CreateShortcut('%PROJ_DIR%dist\FreizeitRezepturverwaltung-debug.lnk'); $s.TargetPath='%PROJ_DIR%dist\_internal\FreizeitRezepturverwaltung-debug.exe'; $s.WorkingDirectory='%PROJ_DIR%dist\_internal'; $s.Save()"
    REM Debug-Installer bauen wenn Inno Setup 6 vorhanden
    set "ISCC_EXE="
    if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC_EXE=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
    if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe"       set "ISCC_EXE=%ProgramFiles%\Inno Setup 6\ISCC.exe"
    if not "%ISCC_EXE%"=="" (
        set /p APP_VERSION=<version.txt
        mkdir installer 2>nul
        echo Building debug installer...
        "%ISCC_EXE%" /DAppVersion=!APP_VERSION! /DAppExe=FreizeitRezepturverwaltung-debug.exe /DNameSuffix=-debug installer.iss
        if errorlevel 1 (
            echo [Warnung] Debug-Installer-Build fehlgeschlagen
        ) else (
            echo Debug-Installer erstellt: installer\
        )
    ) else (
        echo [Hinweis] Inno Setup 6 nicht gefunden - Debug-Installer wurde nicht gebaut.
    )
) else if "%BUILD_MODE%"=="fast" (
    echo Building without onefile ^(faster startup^)...
    %PYTHON_EXE% -m nuitka ^
        --standalone ^
        --output-dir=dist ^
        --output-filename=FreizeitRezepturverwaltung.exe ^
        --include-data-dir=app/templates=app/templates ^
        --include-data-dir=app/static=static ^
        --include-data-file=version.txt=version.txt ^
        --include-package=app ^
        --follow-imports ^
        --windows-console-mode=disable ^
        %NUITKA_VOPT% ^
        app/main.py
    if errorlevel 1 exit /b 1
    REM Modules in _internal verstecken, Launcher in dist\ ablegen
    if exist dist\_internal rmdir /s /q dist\_internal
    move "dist\main.dist" "dist\_internal" > nul
    powershell -NoProfile -Command "$ws=New-Object -ComObject WScript.Shell; $s=$ws.CreateShortcut('%PROJ_DIR%dist\FreizeitRezepturverwaltung.lnk'); $s.TargetPath='%PROJ_DIR%dist\_internal\FreizeitRezepturverwaltung.exe'; $s.WorkingDirectory='%PROJ_DIR%dist\_internal'; $s.Save()"
) else (
    echo Unknown build mode: %BUILD_MODE%
    echo Available modes: standalone, debug, fast
    exit /b 1
)

echo.
echo ========================================
echo Build complete!
echo ========================================
if "%BUILD_MODE%"=="debug" (
    echo Starten:  dist\FreizeitRezepturverwaltung-debug.lnk
    echo Module:   dist\_internal\
) else if "%BUILD_MODE%"=="fast" (
    echo Starten:  dist\FreizeitRezepturverwaltung.lnk
    echo Module:   dist\_internal\
) else (
    echo Output directory: .\dist
)
