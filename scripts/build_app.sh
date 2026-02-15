#!/bin/bash
# Build the self-contained VocalSeparator.app (icon + PyInstaller).
# Run from project root: ./scripts/build_app.sh
# Requires: venv with requirements.txt + pyinstaller installed.

set -e
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

# Build .icns from assets/icon.png so the .app has an icon
if [[ -f "assets/icon.png" ]]; then
  if [[ -f "scripts/build_icon.sh" ]]; then
    echo "Building app icon from assets/icon.png..."
    ./scripts/build_icon.sh || echo "Warning: build_icon.sh failed; .app will use default icon."
  fi
else
  echo "Note: assets/icon.png not found; .app will use default icon. Add icon.png and run ./scripts/build_icon.sh for a custom icon."
fi

echo "Building VocalSeparator.app with PyInstaller..."
if command -v pyinstaller >/dev/null 2>&1; then
  pyinstaller VocalSeparator.spec
else
  python3 -m PyInstaller VocalSeparator.spec
fi

# PyInstaller one-file on macOS often doesn't apply the icon; copy it into the bundle and set Info.plist
APP="$REPO_ROOT/dist/VocalSeparator.app"
RESOURCES="$APP/Contents/Resources"
PLIST="$APP/Contents/Info.plist"
if [[ -f "assets/icon.icns" && -d "$APP" && -f "$PLIST" ]]; then
  mkdir -p "$RESOURCES"
  cp "assets/icon.icns" "$RESOURCES/icon.icns"
  # Tell the .app to use this icon (CFBundleIconFile = filename without .icns)
  /usr/libexec/PlistBuddy -c "Delete :CFBundleIconFile" "$PLIST" 2>/dev/null || true
  /usr/libexec/PlistBuddy -c "Add :CFBundleIconFile string icon" "$PLIST"
  # Force Finder to refresh the bundle's icon
  touch "$APP"
  echo "Applied custom icon to .app bundle."
fi

echo "Done. App: dist/VocalSeparator.app"
