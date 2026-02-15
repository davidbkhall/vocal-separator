#!/bin/bash
# Build the self-contained VocalSeparator.app (icon + PyInstaller).
# Run from project root: ./scripts/build_app.sh
# Requires: venv with requirements.txt + pyinstaller installed.

set -e
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

# GUI requires tkinter; the frozen app needs Tcl/Tk data collected at build time
if ! python3 -c "import tkinter" 2>/dev/null; then
  echo "Error: tkinter is required to build the app (Tcl/Tk must be bundled)." >&2
  echo "Install it, e.g. Homebrew: brew install python-tk@\$(python3 --version | cut -d' ' -f2 | cut -d. -f1-2)" >&2
  exit 1
fi

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
  pyinstaller --noconfirm VocalSeparator.spec
else
  python3 -m PyInstaller --noconfirm VocalSeparator.spec
fi

# PyInstaller one-file on macOS often doesn't apply the icon; copy it into the bundle and set Info.plist
APP="$REPO_ROOT/dist/VocalSeparator.app"
RESOURCES="$APP/Contents/Resources"
PLIST="$APP/Contents/Info.plist"
if [[ -f "assets/icon.icns" && -d "$APP" && -f "$PLIST" ]]; then
  mkdir -p "$RESOURCES"
  cp "assets/icon.icns" "$RESOURCES/icon.icns"
  /usr/libexec/PlistBuddy -c "Delete :CFBundleIconFile" "$PLIST" 2>/dev/null || true
  /usr/libexec/PlistBuddy -c "Add :CFBundleIconFile string icon" "$PLIST"
  touch "$APP"
  echo "Applied custom icon to .app bundle."
elif [[ -d "$APP" ]]; then
  touch "$APP"
fi
if [[ -d "$APP" ]] && [[ ! -f "assets/icon.icns" ]]; then
  echo "Note: Add assets/icon.png and run ./scripts/build_icon.sh, then rebuild, for a custom icon."
fi
echo "Done. App: dist/VocalSeparator.app"
echo "If the app icon does not appear in Finder, run: touch dist/VocalSeparator.app"
