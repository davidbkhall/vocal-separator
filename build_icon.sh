#!/bin/bash
# Create macOS .icns from assets/icon.png (required for .app icon).
# Run once: ./build_icon.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC="${SCRIPT_DIR}/assets/icon.png"
ICONSET="${SCRIPT_DIR}/assets/icon.iconset"
OUT="${SCRIPT_DIR}/assets/icon.icns"

if [[ ! -f "$SRC" ]]; then
  echo "Error: $SRC not found. Add your icon.png to assets/." >&2
  exit 1
fi

mkdir -p "$ICONSET"
# Required sizes for macOS iconset (iconutil is strict about names and sizes)
# Use -s format to keep PNG; sips can misinterpret otherwise
for size in 16 32 128 256 512; do
  sips -z $size $size -s format png "$SRC" --out "$ICONSET/icon_${size}x${size}.png"
done
for size in 16 32 128 256 512; do
  d=$((size * 2))
  sips -z $d $d -s format png "$SRC" --out "$ICONSET/icon_${size}x${size}@2x.png"
done
iconutil -c icns "$ICONSET" -o "$OUT"
rm -rf "$ICONSET"
echo "Created $OUT"
