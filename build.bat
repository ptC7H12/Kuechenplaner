@echo off
REM Build script for Freizeit Rezepturverwaltung (Windows)

setlocal enabledelayedexpansion

set BUILD_MODE=%1
if "%BUILD_MODE%"=="" set BUILD_MODE=standalone

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

REM Clean previous builds
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build

echo Build mode: %BUILD_MODE%
echo.

if "%BUILD_MODE%"=="standalone" (
    echo Building standalone executable...
    python build.py
    if errorlevel 1 exit /b 1
) else if "%BUILD_MODE%"=="debug" (
    echo Building with debug symbols...
    python -m nuitka ^
        --standalone ^
        --output-dir=dist ^
        --output-filename=FreizeitRezepturverwaltung-debug.exe ^
        --include-data-dir=app/templates=app/templates ^
        --include-data-dir=app/static=app/static ^
        --include-package=app ^
        --follow-imports ^
        --debug ^
        --windows-disable-console ^
        app/main.py
    if errorlevel 1 exit /b 1
) else if "%BUILD_MODE%"=="fast" (
    echo Building without onefile ^(faster startup^)...
    python -m nuitka ^
        --standalone ^
        --output-dir=dist ^
        --output-filename=FreizeitRezepturverwaltung.exe ^
        --include-data-dir=app/templates=app/templates ^
        --include-data-dir=app/static=app/static ^
        --include-package=app ^
        --follow-imports ^
        --windows-disable-console ^
        app/main.py
    if errorlevel 1 exit /b 1
) else (
    echo Unknown build mode: %BUILD_MODE%
    echo Available modes: standalone, debug, fast
    exit /b 1
)

echo.
echo ========================================
echo Build complete!
echo ========================================
echo Output directory: .\dist
