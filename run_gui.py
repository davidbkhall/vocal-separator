#!/usr/bin/env python3
"""Launcher for the Vocal Separator GUI (used by PyInstaller bundle)."""

import sys
import traceback


def _log_launch_error() -> None:
    """When frozen, write launch errors to a log file so the user can see why the app didn't open."""
    if not getattr(sys, "frozen", False):
        return
    try:
        from pathlib import Path

        log_dir = Path.home() / "Library" / "Application Support" / "VocalSeparator"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "launch_error.log"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write("\n--- Launch error ---\n")
            traceback.print_exc(file=f)
        sys.stderr.write(f"Error logged to: {log_file}\n")
    except Exception:
        traceback.print_exc()


if __name__ == "__main__":
    try:
        from vocal_separator.app_gui import main

        main()
    except Exception:
        _log_launch_error()
        raise
