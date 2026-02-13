#!/bin/bash
# Build the self-contained VocalSeparator.app (icon + PyInstaller).
# Run from project root: ./build_app.sh
# Requires: venv with requirements.txt + pyinstaller installed.

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Build .icns from assets/icon.png so the .app has an icon
if [[ -f "assets/icon.png" ]]; then
  if [[ -f "build_icon.sh" ]]; then
    echo "Building app icon from assets/icon.png..."
    ./build_icon.sh || echo "Warning: build_icon.sh failed; .app will use default icon."
  fi
else
  echo "Note: assets/icon.png not found; .app will use default icon. Add icon.png and run ./build_icon.sh for a custom icon."
fi

echo "Building VocalSeparator.app with PyInstaller..."
pyinstaller VocalSeparator.spec

echo "Done. App: dist/VocalSeparator.app"
