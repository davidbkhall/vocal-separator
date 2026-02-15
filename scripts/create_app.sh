#!/bin/bash
# Create macOS .app bundle for drag-and-drop (uses project venv and package).
# Run from project root: ./scripts/create_app.sh

set -e
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

# Version from pyproject.toml (single source of truth); fallback to 1.0.0 if extraction fails
APP_VERSION=$(grep '^version = ' pyproject.toml 2>/dev/null | sed 's/version = "\(.*\)"/\1/' | head -n1)
if [ -z "$APP_VERSION" ]; then
  APP_VERSION="1.0.0"
fi

APP_NAME="VocalSeparator"
APP_DIR="$APP_NAME.app"
CONTENTS_DIR="$APP_DIR/Contents"
MACOS_DIR="$CONTENTS_DIR/MacOS"
RESOURCES_DIR="$CONTENTS_DIR/Resources"

# Clean up existing
rm -rf "$APP_DIR"

# Create directory structure
mkdir -p "$MACOS_DIR"
mkdir -p "$RESOURCES_DIR"

# Create Info.plist
cat > "$CONTENTS_DIR/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>VocalSeparator</string>
    <key>CFBundleDisplayName</key>
    <string>Vocal Separator</string>
    <key>CFBundleIdentifier</key>
    <string>com.audioshake.vocalseparator</string>
    <key>CFBundleVersion</key>
    <string>__APP_VERSION__</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleExecutable</key>
    <string>launcher</string>
    <key>CFBundleDocumentTypes</key>
    <array>
        <dict>
            <key>CFBundleTypeName</key>
            <string>Audio File</string>
            <key>CFBundleTypeRole</key>
            <string>Viewer</string>
            <key>LSHandlerRank</key>
            <string>Alternate</string>
            <key>LSItemContentTypes</key>
            <array>
                <string>public.audio</string>
                <string>public.mp3</string>
                <string>public.mpeg-4-audio</string>
                <string>com.microsoft.waveform-audio</string>
                <string>org.xiph.flac</string>
            </array>
        </dict>
        <dict>
            <key>CFBundleTypeName</key>
            <string>Folder</string>
            <key>CFBundleTypeRole</key>
            <string>Viewer</string>
            <key>LSHandlerRank</key>
            <string>Alternate</string>
            <key>LSItemContentTypes</key>
            <array>
                <string>public.folder</string>
            </array>
        </dict>
    </array>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF
sed -i '' "s/__APP_VERSION__/$APP_VERSION/g" "$CONTENTS_DIR/Info.plist"

# Create launcher script (cd to repo root, use venv, run installed package)
cat > "$MACOS_DIR/launcher" << EOF
#!/bin/bash
cd "$REPO_ROOT"
if [ -d "venv" ]; then
    source venv/bin/activate
fi
exec python3 -m vocal_separator.app_gui "\$@"
EOF

chmod +x "$MACOS_DIR/launcher"

echo "✅ Created $APP_DIR"
echo ""
echo "To use:"
echo "  1. Run: pip install -e .  (from project root)"
echo "  2. Double-click $APP_DIR to open"
echo "  3. Drag audio files or folders onto the app icon"
echo ""
echo "Make sure you've set up your .env file with your API key!"
