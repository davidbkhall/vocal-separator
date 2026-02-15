# Audioshake Voice Separator

Extract vocals from audio using the [Audioshake API](https://developer.audioshake.ai/). CLI, batch processing, and a macOS GUI/drag-and-drop app.

## Features

- Extract vocals (and instrumentals) from MP3, WAV, FLAC, M4A, OGG, AAC, WMA
- Batch process folders with optional parallel workers
- macOS: GUI app or drag-and-drop droplet; optional standalone `.app` bundle

## Requirements

- Python 3.10+
- [Audioshake API key](https://www.audioshake.ai) (sign up, then get key from dashboard/settings)
- macOS only for the GUI/drag-and-drop and for building the standalone app

## Setup

```bash
cd audioshake-separator
python3 -m venv venv
source venv/bin/activate
pip install -e .
cp .env.example .env
# Edit .env and add AUDIOSHAKE_API_KEY=your_key
```

This installs the package in editable mode and registers the `audioshake-separate`, `audioshake-batch`, and `vocalseparator` commands.

## Usage

### CLI — single file

```bash
audioshake-separate song.mp3
audioshake-separate song.wav -o ./vocals
```

Or: `python -m audioshake_separator.separator song.mp3`

### CLI — batch

```bash
audioshake-batch ./music
audioshake-batch ./music -r -o ./vocals -w 4   # recursive, 4 workers
```

Or: `python -m audioshake_separator.batch ./music`

### macOS: quick GUI / drag-and-drop

Uses your project venv and `.env`:

```bash
./scripts/create_app.sh
# Then double-click VocalSeparator.app from the project directory
```

Open the app → **Settings** to set your API key and options. **Main** tab: add files or folder, choose output dir, click **Start**.

### macOS: standalone .app (shareable bundle)

Build a self-contained `VocalSeparator.app` with Python and dependencies inside (no need for a venv on the target machine):

```bash
pip install pyinstaller
./scripts/build_app.sh
```

Output: **`dist/VocalSeparator.app`**. Move to Applications or share. On first run, settings and API key are stored under `~/Library/Application Support/VocalSeparator/`.

- **Icon:** `./scripts/build_app.sh` builds `assets/icon.icns` from `assets/icon.png` and applies it. If the icon doesn’t appear, run `touch dist/VocalSeparator.app` or restart Finder.
- **If `scripts/build_icon.sh` fails:** create `assets/icon.icns` elsewhere (e.g. [cloudconvert.com/png-to-icns](https://cloudconvert.com/png-to-icns)) and run `./scripts/build_app.sh` again.
- **tkinter:** If you use Homebrew Python and get “No module named '_tkinter'”, run `brew install python-tk@3.14` (or match your Python version).

Alternative (py2app): Python 3.12, setuptools &lt;69, then `pip install -e . py2app` and `python setup.py py2app`.

## CLI options

| Command               | Options |
|-----------------------|---------|
| `audioshake-separate` | `input` (file), `-o/--output` (default: `./output`) |
| `audioshake-batch`    | `input` (dir or files), `-o/--output`, `-r/--recursive`, `-w/--workers` (default: 2) |

## Output

Per input file you get (names follow Audioshake task output):

- `{basename}_vocals.wav`
- `{basename}_instrumental.wav`

(Exact stems depend on the task target; see Settings in the GUI or [Tasks API](https://developer.audioshake.ai/).)

## Project structure

```
audioshake-separator/
├── src/audioshake_separator/   # Installable package
│   ├── separator.py            # Core API + single-file CLI
│   ├── batch.py                # Batch CLI
│   ├── app_gui.py              # GUI (used by .app bundle)
│   └── droplet.py              # Drag-and-drop launcher (macOS)
├── scripts/
│   ├── build_app.sh            # Build standalone .app (PyInstaller)
│   ├── build_icon.sh           # Build icon.icns from assets/icon.png
│   └── create_app.sh          # Create dev .app using project venv
├── run_gui.py                  # Launcher for PyInstaller bundle
├── VocalSeparator.spec         # PyInstaller spec
├── setup.py                    # py2app (alternative macOS build)
├── assets/
│   └── icon.png                # App icon source
└── tests/
```

## Development

```bash
pip install -e .
pip install -r requirements-dev.txt
pre-commit install
```

Then `git commit` runs ruff + mypy. Manual run: `pre-commit run --all-files`.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| **AUDIOSHAKE_API_KEY not found** | Create `.env` from `.env.example`, add your key. |
| **Upload failed / 401** | Check API key and quota; invalid/expired key shows a clear auth error. |
| **Drag-and-drop app doesn’t work** | Run `./scripts/create_app.sh` from project root; run `pip install -e .` then `python -m audioshake_separator.droplet <file>` to see errors. |
| **No module named '_tkinter'** | Homebrew: `brew install python-tk@3.14` (or your Python version). |
