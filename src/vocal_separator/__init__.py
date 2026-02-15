"""
Audioshake Voice Separator – extract vocals from audio via Audioshake API.
"""

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
]
