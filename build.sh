#!/bin/bash
# Build script for Freizeit Rezepturverwaltung
# Supports different build modes

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default build mode
BUILD_MODE="${1:-standalone}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Freizeit Rezepturverwaltung Build${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if Nuitka is installed
if ! python3 -m nuitka --version &> /dev/null; then
    echo -e "${RED}Error: Nuitka is not installed${NC}"
    echo "Install it with: pip install nuitka"
    exit 1
fi

# Clean previous builds
if [ -d "dist" ]; then
    echo -e "${YELLOW}Cleaning previous builds...${NC}"
    rm -rf dist
fi

if [ -d "build" ]; then
    rm -rf build
fi

echo -e "${GREEN}Build mode: ${BUILD_MODE}${NC}"
echo ""

case "$BUILD_MODE" in
    "standalone")
        echo "Building standalone executable..."
        python3 build.py
        ;;

    "debug")
        echo "Building with debug symbols..."
        python3 -m nuitka \
            --standalone \
            --output-dir=dist \
            --output-filename=FreizeitRezepturverwaltung-debug \
            --include-data-dir=app/templates=app/templates \
            --include-data-dir=app/static=app/static \
            --include-package=app \
            --follow-imports \
            --debug \
            app/main.py
        ;;

    "fast")
        echo "Building without onefile (faster startup)..."
        python3 -m nuitka \
            --standalone \
            --output-dir=dist \
            --output-filename=FreizeitRezepturverwaltung \
            --include-data-dir=app/templates=app/templates \
            --include-data-dir=app/static=app/static \
            --include-package=app \
            --follow-imports \
            app/main.py
        ;;

    *)
        echo -e "${RED}Unknown build mode: $BUILD_MODE${NC}"
        echo "Available modes: standalone, debug, fast"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Build complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo "Output directory: ./dist"
