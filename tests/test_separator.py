"""
Tests for separator.py
"""

import os
from pathlib import Path
from unittest.mock import patch

import responses

from vocal_separator.separator import (
    API_BASE_URL,
    check_api_key,
    create_task,
    download_stems,
    get_headers,
    is_valid_audio_file,
    upload_file,
    wait_for_completion,
)


class TestValidation:
    """Tests for validation functions."""

    def test_valid_audio_extensions(self):
        """Test that common audio formats are recognized."""
        valid_files = [
            Path("song.mp3"),
            Path("song.MP3"),
            Path("audio.wav"),
            Path("audio.WAV"),
            Path("music.flac"),
            Path("podcast.m4a"),
            Path("sound.ogg"),
            Path("track.aac"),
        ]
        for f in valid_files:
            assert is_valid_audio_file(f), f"{f} should be valid"

    def test_invalid_audio_extensions(self):
        """Test that non-audio formats are rejected."""
        invalid_files = [
            Path("document.pdf"),
            Path("image.png"),
            Path("video.mp4"),
            Path("text.txt"),
            Path("noextension"),
        ]
        for f in invalid_files:
            assert not is_valid_audio_file(f), f"{f} should be invalid"

    def test_check_api_key_missing(self):
        """Test that missing API key returns False."""
        with patch.dict(os.environ, {}, clear=True):
            assert check_api_key() is False

    def test_check_api_key_present(self):
        """Test that present API key returns True."""
        with patch("vocal_separator.separator.get_api_key", return_value="test_key_123"):
            assert check_api_key() is True

    def test_get_headers(self):
        """Test that headers include x-api-key per AudioShake docs."""
        with patch("vocal_separator.separator.get_api_key", return_value="test_key_123"):
            headers = get_headers()
            assert "x-api-key" in headers
            assert headers["x-api-key"] == "test_key_123"


class TestUpload:
    """Tests for file upload functionality."""

    @responses.activate
    def test_upload_file_success(self, tmp_path):
        """Test successful file upload."""
        # Create a test file
        test_file = tmp_path / "test.mp3"
        test_file.write_bytes(b"fake audio content")

        # Mock the API response (POST /assets per AudioShake docs)
        responses.add(
            responses.POST,
            f"{API_BASE_URL}/assets",
            json={"id": "asset_123"},
            status=200,
        )

        with patch("vocal_separator.separator.get_api_key", return_value="test_key"):
            asset_id = upload_file(test_file, quiet=True)

        assert asset_id == "asset_123"

    @responses.activate
    def test_upload_file_failure(self, tmp_path):
        """Test failed file upload (POST /assets returns 400)."""
        test_file = tmp_path / "test.mp3"
        test_file.write_bytes(b"fake audio content")

        responses.add(
            responses.POST,
            f"{API_BASE_URL}/assets",
            json={"error": "Invalid file"},
            status=400,
        )

        with patch("vocal_separator.separator.get_api_key", return_value="test_key"):
            asset_id = upload_file(test_file, quiet=True)

        assert asset_id is None


class TestTaskCreation:
    """Tests for task creation (POST /tasks)."""

    @responses.activate
    def test_create_task_success(self):
        """Test successful task creation."""
        responses.add(
            responses.POST,
            f"{API_BASE_URL}/tasks",
            json={"id": "task_456"},
            status=201,
        )

        with patch("vocal_separator.separator.get_api_key", return_value="test_key"):
            task_id = create_task(
                "asset_123", [{"model": "vocals", "formats": ["wav"]}], quiet=True
            )

        assert task_id == "task_456"

    @responses.activate
    def test_create_task_failure(self):
        """Test failed task creation."""
        responses.add(
            responses.POST,
            f"{API_BASE_URL}/tasks",
            json={"error": "Invalid asset"},
            status=400,
        )

        with patch("vocal_separator.separator.get_api_key", return_value="test_key"):
            task_id = create_task(
                "invalid_asset", [{"model": "vocals", "formats": ["wav"]}], quiet=True
            )

        assert task_id is None


class TestTaskPolling:
    """Tests for task status polling (GET /tasks/{id})."""

    @responses.activate
    def test_wait_for_completion_success(self):
        """Test successful task completion (all targets completed)."""
        responses.add(
            responses.GET,
            f"{API_BASE_URL}/tasks/task_123",
            json={
                "id": "task_123",
                "targets": [
                    {
                        "status": "completed",
                        "output": [{"name": "vocals", "link": "https://example.com/vocals.wav"}],
                    }
                ],
            },
            status=200,
        )

        with patch("vocal_separator.separator.get_api_key", return_value="test_key"):
            result = wait_for_completion("task_123", poll_interval=0, quiet=True)

        assert result is not None
        assert result["targets"][0]["status"] == "completed"

    @responses.activate
    def test_wait_for_completion_failure(self):
        """Test failed task (target status failed)."""
        responses.add(
            responses.GET,
            f"{API_BASE_URL}/tasks/task_123",
            json={
                "id": "task_123",
                "targets": [{"status": "failed", "error": "Processing error"}],
            },
            status=200,
        )

        with patch("vocal_separator.separator.get_api_key", return_value="test_key"):
            result = wait_for_completion("task_123", poll_interval=0, quiet=True)

        assert result is None


class TestDownload:
    """Tests for stem downloading."""

    @responses.activate
    def test_download_stems_success(self, tmp_path):
        """Test successful stem download."""
        output_dir = tmp_path / "output"

        # Mock the download URL
        responses.add(
            responses.GET,
            "https://example.com/vocals.wav",
            body=b"fake audio data",
            status=200,
        )

        task_data = {
            "targets": [{"output": [{"name": "vocals", "link": "https://example.com/vocals.wav"}]}]
        }

        saved = download_stems(task_data, output_dir, "song.mp3", quiet=True)

        assert len(saved) == 1
        assert saved[0].exists()
        assert "vocals" in saved[0].name

    def test_download_stems_empty(self, tmp_path):
        """Test handling of empty output (no targets or empty output)."""
        output_dir = tmp_path / "output"
        task_data = {"targets": []}

        saved = download_stems(task_data, output_dir, "song.mp3", quiet=True)

        assert len(saved) == 0
