# Vocal Separator

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
cd vocal-separator
python3 -m venv venv
source venv/bin/activate
pip install -e .
cp .env.example .env
# Edit .env and add AUDIOSHAKE_API_KEY=your_key
```

This installs the package in editable mode and registers the `vocal-separate`, `vocal-batch`, and `vocalseparator` commands.

## Usage

### CLI — single file

```bash
vocal-separate song.mp3
vocal-separate song.wav -o ./vocals
vocal-separate track.flac -o ./stems -m instrumental -f mp3 --variant high_quality --residual
```

Or: `python -m vocal_separator.separator song.mp3`

### CLI — batch

```bash
vocal-batch ./music
vocal-batch ./music -r -o ./vocals -w 4
vocal-batch ./music -m instrumental -f mp3 --variant high_quality
```

Or: `python -m vocal_separator.batch ./music`

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
- **tkinter:** If you use Homebrew Python and get “No module named '_tkinter'”, run `brew install python-tk@3.14` (or match your Python version). The .app build must use a Python that has tkinter so Tcl/Tk gets bundled; otherwise the frozen app will show “No module named 'tkinter'”.

Alternative (py2app): Python 3.12, setuptools &lt;69, then `pip install -e . py2app` and `python setup.py py2app`.

## CLI options

Options match the Audioshake API (same as in the GUI Settings). Run `vocal-separate --help` or `vocal-batch --help` for details.

| Command | Option | Description |
|---------|--------|-------------|
| **vocal-separate** | `input` | Input audio file (required) |
| | `-o`, `--output` | Output directory (default: `./output`) |
| | `-m`, `--model` | Target model: vocals, instrumental, drums, etc. (default: vocals) |
| | `-f`, `--format` | Output format: wav, mp3, flac, aiff (default: wav) |
| | `--variant` | Optional variant, e.g. high_quality |
| | `--residual` | Include residual stem when supported |
| **vocal-batch** | `input` | Directory or list of audio files (required) |
| | `-o`, `--output` | Output directory (default: `./output`) |
| | `-r`, `--recursive` | Search subdirectories for audio files |
| | `-w`, `--workers` | Parallel jobs (default: 2) |
| | `-m`, `--model` | Target model (default: vocals) |
| | `-f`, `--format` | Output format (default: wav) |
| | `--variant` | Optional variant |
| | `--residual` | Include residual stem when supported |

**Example (single file with options):**

```bash
vocal-separate song.mp3 -o ./vocals -m vocals -f wav --variant high_quality
```

## Output

Per input file you get stems named by the task target (e.g. `{basename}_vocals.wav`, `{basename}_instrumental.wav`). The file extension matches the chosen output format (wav, mp3, flac, or aiff). See the [Audioshake Tasks API](https://developer.audioshake.ai/) for target and variant details.

## Project structure

```
vocal-separator/
├── src/vocal_separator/   # Installable package
│   ├── separator.py            # Core API + single-file CLI
│   ├── batch.py                # Batch CLI
│   ├── app_gui.py              # GUI (used by .app bundle)
│   └── droplet.py              # Drag-and-drop launcher (macOS)
├── scripts/
│   ├── build_app.sh            # Build standalone .app (PyInstaller)
│   ├── build_icon.sh           # Build icon.icns from assets/icon.png
│   └── create_app.sh           # Create dev .app using project venv
├── pyproject.toml              # Package config and script entry points
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
| **VocalSeparator.app does nothing when opened** | Run the binary from Terminal to see the error: `./dist/VocalSeparator.app/Contents/MacOS/VocalSeparator` (or `./dist/VocalSeparator/VocalSeparator` if no .app). Check `~/Library/Application Support/VocalSeparator/launch_error.log` for the traceback. If it says “No module named 'tkinter'”, rebuild with a Python that has tkinter: `brew install python-tk@3.11` (or your version), recreate the venv with that Python, then `./scripts/build_app.sh` again. |
| **App icon doesn’t appear** | Ensure `assets/icon.png` exists before building; `./scripts/build_app.sh` creates `icon.icns` and copies it into the .app. If the icon still doesn’t show, run `touch dist/VocalSeparator.app` or log out and back in to refresh Finder. |
| **AUDIOSHAKE_API_KEY not found** | Create `.env` from `.env.example`, add your key. |
| **Upload failed / 401** | Check API key and quota; invalid/expired key shows a clear auth error. |
| **Drag-and-drop app doesn’t work** | Run `./scripts/create_app.sh` from project root; run `pip install -e .` then `python -m vocal_separator.droplet <file>` to see errors. |
| **No module named '_tkinter'** | Homebrew: `brew install python-tk@3.14` (or your Python version). |
