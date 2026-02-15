"""
Audioshake Voice Separator – extract vocals from audio via Audioshake API.
"""

import re
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

try:
    __version__ = version("vocal-separator")
except PackageNotFoundError:
    # Run from source without install: read from pyproject.toml
    _pyproject = Path(__file__).resolve().parent.parent.parent / "pyproject.toml"
    if _pyproject.exists():
        _m = re.search(r'version\s*=\s*"([^"]+)"', _pyproject.read_text())
        __version__ = _m.group(1) if _m else "1.0.0"
    else:
        __version__ = "1.0.0"

from vocal_separator.separator import (
    API_BASE_URL,
    AUTH_ERROR_MSG,
    VALID_EXTENSIONS,
    AuthenticationError,
    check_api_key,
    get_api_key,
    is_valid_audio_file,
    separate_file,
)

__all__ = [
    "AUTH_ERROR_MSG",
    "API_BASE_URL",
    "VALID_EXTENSIONS",
    "AuthenticationError",
    "check_api_key",
    "get_api_key",
    "is_valid_audio_file",
    "separate_file",
    "__version__",
]
