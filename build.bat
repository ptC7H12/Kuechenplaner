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
    echo Building with console enabled for debug output ^(RAM-optimized^)...
    python -m nuitka ^
        --standalone ^
        --output-dir=dist ^
        --output-filename=FreizeitRezepturverwaltung-debug.exe ^
        --include-data-dir=app/templates=app/templates ^
        --include-data-dir=app/static=static ^
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
        --nofollow-import-to=sqlalchemy.dialects.postgresql ^
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
