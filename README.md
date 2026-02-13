# Audioshake Voice Separator

A lightweight CLI tool to extract vocals from audio files using the Audioshake API.
Includes batch processing and a macOS drag-and-drop app.

## Features

- 🎵 Extract vocals from any audio file
- 📁 Batch process entire folders
- 🖱️ Drag-and-drop macOS app
- ⚡ Parallel processing for speed
- 🍎 Optimized for Apple Silicon

## Requirements

- Python 3.9+
- macOS (for drag-and-drop app) or any OS (for CLI)
- Audioshake API key

## Setup

### 1. Clone/download this project

### 2. Create virtual environment and install dependencies

```bash
cd audioshake-separator
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```plaintext

### 3. Configure your API key

```bash
cp .env.example .env
# Edit .env and add your Audioshake API key
```plaintext

### 4. (Optional) Create the drag-and-drop app

```bash
chmod +x create_app.sh
./create_app.sh
```plaintext

## Getting an API Key

1. Visit [audioshake.ai](https://www.audioshake.ai)
2. Sign up for an account
3. Navigate to your dashboard/API settings
4. Generate an API key
5. Copy it to your `.env` file

---

## Usage

### Single File (CLI)

```bash
python separator.py song.mp3
python separator.py song.wav -o ./vocals
```plaintext

### Batch Processing

```bash
# Process all audio in a folder
python batch.py ./music

# Recursive (include subfolders)
python batch.py ./music -r

# Custom output and parallel jobs
python batch.py ./music -o ./vocals -w 4
```plaintext

### GUI App (macOS)

1. Install dependencies: `pip install -r requirements.txt` (or use a venv; see Setup).
2. Run `./create_app.sh` to create **VocalSeparator.app**
3. Double-click the app to open the GUI
4. **Main tab:** Add files or a folder, choose output directory, then click **Start**. Use **Stop** to cancel. Progress and per-file status are shown.
5. **Settings tab:** Enter your API key, optional Audioshake format/job name, and enable a log file if desired. Click **Save settings**.
6. Move the `.app` to Applications or keep it in the project folder (it uses this project’s Python and `.env`)

### Building a standalone macOS app (bundle)

To build a **self-contained** `.app` that includes Python and all dependencies (so others can run it without installing Python or pip packages):

1. **Use Python 3.12 or 3.13** — py2app does not support Python 3.14 yet (`pkg_resources` / `importlib.resources` changes). Install if needed: `brew install python@3.12`.
2. Create a venv with that Python and install deps:
   ```bash
   cd audioshake-separator
   python3.12 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   pip install py2app
   ```
3. Build the bundle:
   ```bash
   python setup.py py2app
   ```
4. The app is created at **`dist/VocalSeparator.app`**. You can move it to Applications or share it.
5. On first run, the bundled app stores settings and API key in **`~/Library/Application Support/VocalSeparator/`** (create that folder and add a `.env` with your API key there if you pre-configure).

**Development build** (faster; uses your current Python and installed packages, no copy of dependencies):
   ```bash
   python setup.py py2app -A
   ```

**Requirements:** Build on macOS with a Python that has tkinter (e.g. `brew install python-tk@3.12` for Python 3.12).

**If the build fails:** Use Python 3.12 or 3.13 for the venv and build (see step 1). If you see “No module named 'pkg_resources'” or “cannot import name '_files' from 'importlib.resources'”, you are on Python 3.14 — recreate the venv with `python3.12 -m venv venv`. If your shell’s `python` points to another interpreter, use the venv or run e.g. `python3.12 setup.py py2app`.

---

## CLI Options

### `separator.py`

| Option | Description |
|--------|-------------|
| `input` | Input audio file |
| `-o, --output` | Output directory (default: `./output`) |

### `batch.py`

| Option | Description |
|--------|-------------|
| `input` | Input directory or files |
| `-o, --output` | Output directory (default: `./output`) |
| `-r, --recursive` | Search subdirectories |
| `-w, --workers` | Parallel jobs (default: 2) |

---

## Supported Formats

- MP3
- WAV
- FLAC
- M4A
- OGG
- AAC
- WMA

---

## Output

For each input file, you'll get:
- `{filename}_vocals.wav` - Isolated vocal track
- `{filename}_instrumental.wav` - Background/instrumental track

---

## Development

### Pre-commit hooks (linting)

To run ruff and mypy automatically before each commit:

```bash
pip install -r requirements-dev.txt
pre-commit install
```

After that, every `git commit` will run formatting, linting, and type checking. To run the hooks manually on all files:

```bash
pre-commit run --all-files
```

---

## Troubleshooting

**"No module named '_tkinter'" when running the GUI**

If you use Homebrew Python, install tkinter for your Python version:

```bash
brew install python-tk@3.14   # or python-tk@3.12, etc. to match your python3
```

Then run `python3 app_gui.py` again.

**"AUDIOSHAKE_API_KEY not found"**
- Make sure you've created a `.env` file with your API key
- Check that the key is correct

**"Upload failed"**
- Check your internet connection
- Verify your API key is valid
- Ensure the file isn't corrupted

**Drag-and-drop app doesn't work**
- Make sure you ran `create_app.sh` from the project directory
- Check that the virtual environment is set up
- Try running `python droplet.py <file>` directly to see errors
