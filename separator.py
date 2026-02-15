#!/usr/bin/env python3
"""
Voice Separation CLI using Audioshake API
Extracts vocals from audio files
"""

import argparse
import os
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import cast

import requests
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

load_dotenv()

console = Console()

# Official Tasks API per https://developer.audioshake.ai/
API_BASE_URL = "https://api.audioshake.ai"

# Raised when the API returns 401 so the GUI/log can show a clear auth message
AUTH_ERROR_MSG = (
    "Authentication failed. Your API key may be invalid or expired. "
    "Check your key in Settings and try again."
)


class AuthenticationError(Exception):
    """Raised when Audioshake API returns 401 Unauthorized."""

    def __init__(self) -> None:
        super().__init__(AUTH_ERROR_MSG)


VALID_EXTENSIONS = {".mp3", ".wav", ".flac", ".m4a", ".ogg", ".aac", ".wma"}


def get_api_key() -> str | None:
    """Return current API key from environment (so GUI save updates take effect)."""
    return os.getenv("AUDIOSHAKE_API_KEY")


def check_api_key() -> bool:
    """Verify API key is configured."""
    if not get_api_key():
        console.print("\n[red]❌ AUDIOSHAKE_API_KEY not found![/red]\n")
        console.print("To get started:")
        console.print("  1. Get your API key from [link]https://www.audioshake.ai[/link]")
        console.print("  2. Copy .env.example to .env")
        console.print("  3. Add your API key to the .env file\n")
        return False
    return True


def get_headers() -> dict:
    """Return headers for API requests (x-api-key per AudioShake docs)."""
    key = get_api_key() or ""
    return {"x-api-key": key}


def is_valid_audio_file(file_path: Path) -> bool:
    """Check if file is a supported audio format."""
    return file_path.suffix.lower() in VALID_EXTENSIONS


def upload_file(file_path: Path, quiet: bool = False) -> str | None:
    """Upload audio file via POST /assets and return asset ID."""
    if not quiet:
        console.print(f"[blue]📤 Uploading:[/blue] {file_path.name}")

    url = f"{API_BASE_URL}/assets"

    try:
        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f)}
            response = requests.post(url, headers=get_headers(), files=files, timeout=300)

        if response.status_code == 401:
            raise AuthenticationError()
        if response.status_code != 200:
            console.print(f"[red]❌ Upload failed ({response.status_code}):[/red] {response.text}")
            return None

        data = response.json()
        asset_id = data.get("id")
        if not quiet:
            console.print(f"[green]✅ Uploaded[/green] (Asset ID: {asset_id})")
        return cast(str | None, asset_id)

    except requests.exceptions.RequestException as e:
        console.print(f"[red]❌ Upload error:[/red] {e}")
        return None


def build_target(
    model: str,
    formats: list[str],
    variant: str | None = None,
    residual: bool = False,
    language: str | None = None,
) -> dict:
    """Build a Tasks API target object (model + formats + optional variant/residual/language)."""
    target: dict = {"model": model, "formats": formats}
    if variant:
        target["variant"] = variant
    if residual:
        target["residual"] = True
    if language:
        target["language"] = language
    return target


def create_task(
    asset_id: str,
    targets: list[dict],
    quiet: bool = False,
) -> str | None:
    """Create a task via POST /tasks. Returns task ID."""
    if not quiet:
        console.print("[blue]🎵 Starting separation task...[/blue]")

    url = f"{API_BASE_URL}/tasks"
    payload = {"assetId": asset_id, "targets": targets}

    try:
        response = requests.post(
            url,
            headers={**get_headers(), "Content-Type": "application/json"},
            json=payload,
            timeout=60,
        )

        if response.status_code == 401:
            raise AuthenticationError()
        if response.status_code not in [200, 201]:
            console.print(
                f"[red]❌ Task creation failed ({response.status_code}):[/red] {response.text}"
            )
            return None

        task_id = response.json().get("id")
        if not quiet:
            console.print(f"[green]✅ Task started[/green] (Task ID: {task_id})")
        return cast(str | None, task_id)

    except requests.exceptions.RequestException as e:
        console.print(f"[red]❌ Task creation error:[/red] {e}")
        return None


def _task_done(data: dict) -> tuple[bool, bool]:
    """Return (all_completed, any_failed) from GET /tasks/{id} response."""
    targets = data.get("targets") or []
    if not targets:
        return False, False
    statuses = [t.get("status") for t in targets]
    all_done = all(s == "completed" for s in statuses)
    any_failed = any(s == "failed" for s in statuses)
    return all_done, any_failed


def wait_for_completion(
    task_id: str,
    poll_interval: int = 5,
    quiet: bool = False,
    cancel_check: Callable[[], bool] | None = None,
) -> dict | None:
    """Poll GET /tasks/{id} until all targets complete. Return task data or None."""
    url = f"{API_BASE_URL}/tasks/{task_id}"

    if quiet:
        while True:
            try:
                if cancel_check and cancel_check():
                    return None
                response = requests.get(url, headers=get_headers(), timeout=30)
                if response.status_code == 401:
                    raise AuthenticationError()
                if response.status_code != 200:
                    return None

                data = response.json()
                all_done, any_failed = _task_done(data)
                if any_failed:
                    return None
                if all_done:
                    return cast(dict, data)

                time.sleep(poll_interval)
            except requests.exceptions.RequestException:
                return None
    else:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            prog_task = progress.add_task("⏳ Processing audio...", total=None)

            while True:
                try:
                    if cancel_check and cancel_check():
                        return None
                    response = requests.get(url, headers=get_headers(), timeout=30)

                    if response.status_code == 401:
                        raise AuthenticationError()
                    if response.status_code != 200:
                        console.print(f"[red]❌ Status check failed:[/red] {response.text}")
                        return None

                    data = response.json()
                    all_done, any_failed = _task_done(data)
                    if any_failed:
                        for t in data.get("targets") or []:
                            if t.get("status") == "failed":
                                err = t.get("error", "Unknown error")
                                console.print(f"\n[red]❌ Task failed:[/red] {err}")
                                break
                        return None
                    if all_done:
                        progress.update(prog_task, description="[green]✅ Processing complete!")
                        return cast(dict, data)

                    time.sleep(poll_interval)

                except requests.exceptions.RequestException as e:
                    console.print(f"[red]❌ Connection error:[/red] {e}")
                    return None


def download_stems(
    task_data: dict, output_dir: Path, original_name: str, quiet: bool = False
) -> list[Path]:
    """Download output files from completed task (targets[].output[].link)."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Tasks API: each target has output: [ { name, link, format, ... } ]
    stems: list[tuple[str, str]] = []
    for target in task_data.get("targets") or []:
        for out in target.get("output") or []:
            name = out.get("name") or "output"
            link = out.get("link")
            if link:
                stems.append((name, link))

    if not stems:
        if not quiet:
            console.print("[yellow]⚠️ No output files found.[/yellow]")
        return []

    if not quiet:
        console.print(f"\n[blue]📥 Downloading {len(stems)} file(s)...[/blue]")

    saved_files = []
    base_name = Path(original_name).stem

    for stem_name, stem_url in stems:
        extension = Path(stem_url).suffix.split("?")[0] or ".wav"
        output_file = output_dir / f"{base_name}_{stem_name}{extension}"

        try:
            response = requests.get(stem_url, stream=True, timeout=300)

            if response.status_code == 200:
                with open(output_file, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                if not quiet:
                    console.print(f"   [green]✅[/green] {output_file.name}")
                saved_files.append(output_file)
            else:
                if not quiet:
                    console.print(f"   [red]❌[/red] Failed: {stem_name}")

        except requests.exceptions.RequestException as e:
            if not quiet:
                console.print(f"   [red]❌[/red] Download error: {e}")

    return saved_files


def separate_file(
    input_file: Path,
    output_dir: Path,
    quiet: bool = False,
    cancel_check: Callable[[], bool] | None = None,
    model: str = "vocals",
    output_format: str = "wav",
    variant: str | None = None,
    residual: bool = False,
    language: str | None = None,
) -> bool:
    """
    Separate a single file using the Tasks API. Returns True on success.
    Target options: model, output_format, optional variant, residual, language.
    """
    if not input_file.exists():
        if not quiet:
            console.print(f"[red]❌ File not found:[/red] {input_file}")
        return False

    if not is_valid_audio_file(input_file):
        if not quiet:
            console.print(f"[yellow]⚠️ Skipping unsupported file:[/yellow] {input_file.name}")
        return False

    asset_id = upload_file(input_file, quiet)
    if not asset_id:
        return False

    target = build_target(
        model=model,
        formats=[output_format],
        variant=variant or None,
        residual=residual,
        language=language,
    )
    task_id = create_task(asset_id, [target], quiet=quiet)
    if not task_id:
        return False

    task_data = wait_for_completion(task_id, quiet=quiet, cancel_check=cancel_check)
    if not task_data:
        return False

    saved = download_stems(task_data, output_dir, input_file.name, quiet)
    return len(saved) > 0


def separate(input_file: Path, output_dir: Path):
    """Main separation workflow for single file."""
    console.print("\n[bold cyan]🎧 Audioshake Voice Separator[/bold cyan]\n")

    if not check_api_key():
        sys.exit(1)

    try:
        success = separate_file(input_file, output_dir)
    except AuthenticationError as e:
        console.print(f"\n[red]❌ {e}[/red]\n")
        sys.exit(1)

    if success:
        console.print(f"\n[bold green]🎉 Done![/bold green] Files saved to: {output_dir}\n")
    else:
        console.print("\n[red]❌ Separation failed.[/red]\n")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Extract vocals from audio using Audioshake API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s song.mp3
  %(prog)s song.wav -o ./vocals
  %(prog)s podcast.mp3 --output ~/Desktop/separated

For batch processing, use: python batch.py <directory>
        """,
    )

    parser.add_argument(
        "input",
        type=Path,
        help="Input audio file (MP3, WAV, FLAC, M4A, etc.)",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("./output"),
        help="Output directory (default: ./output)",
    )

    args = parser.parse_args()
    separate(args.input, args.output)


if __name__ == "__main__":
    main()
