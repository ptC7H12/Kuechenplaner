@echo off
REM Build script for Freizeit Rezepturverwaltung (Windows)

setlocal enabledelayedexpansion

set BUILD_MODE=%1
if "%BUILD_MODE%"=="" set BUILD_MODE=standalone
set CLEAN_BUILD=%2
set PROJ_DIR=%~dp0

echo ========================================
echo Freizeit Rezepturverwaltung Build
echo ========================================
echo.

REM Check if Nuitka is installed
python -m nuitka --version >nul 2>&1
if errorlevel 1 (
    echo Error: Nuitka is not installed
    echo Install it with: pip install nuitka
    exit /b 1
)

REM Always clean dist (output), only clean build cache if "clean" is passed
if exist dist rmdir /s /q dist
if /i "%CLEAN_BUILD%"=="clean" (
    echo Cleaning build cache...
    if exist build rmdir /s /q build
) else (
    echo Keeping build cache for incremental compilation.
    echo Use '.\build.bat %BUILD_MODE% clean' to force a full rebuild.
)

echo Build mode: %BUILD_MODE%
echo.

if "%BUILD_MODE%"=="standalone" (
    echo Building standalone executable...
    python build.py
    if errorlevel 1 exit /b 1
) else if "%BUILD_MODE%"=="debug" (
    echo Building with console enabled for debug output ^(RAM-optimized^)...
    python -m nuitka ^
        --standalone ^
        --output-dir=dist ^
        --output-filename=FreizeitRezepturverwaltung-debug.exe ^
        --include-data-dir=app/templates=app/templates ^
        --include-data-dir=app/static=static ^
        --include-data-dir=alembic=alembic_migration ^
        --include-data-file=alembic.ini=alembic.ini ^
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
    python -m nuitka ^
        --standalone ^
        --output-dir=dist ^
        --output-filename=FreizeitRezepturverwaltung.exe ^
        --include-data-dir=app/templates=app/templates ^
        --include-data-dir=app/static=static ^
        --include-package=app ^
        --follow-imports ^
        --windows-console-mode=disable ^
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
