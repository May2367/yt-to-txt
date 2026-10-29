"""Audio download helpers built around yt-dlp."""

from __future__ import annotations

import re
import tempfile
from pathlib import Path
from typing import Any, TypedDict

from config import TEMP_AUDIO_PREFIX


class VideoMetadata(TypedDict):
    title: str
    video_id: str
    url: str
    duration: int | None


class DownloadResult(TypedDict):
    audio_path: Path
    metadata: VideoMetadata


class AudioDownloadError(RuntimeError):
    """Raised when audio cannot be downloaded or prepared."""


def _safe_id(raw_id: str | None) -> str:
    if not raw_id:
        return "unknown_video"
    return re.sub(r"[^A-Za-z0-9_-]+", "_", raw_id).strip("_") or "unknown_video"


def download_audio(youtube_url: str) -> DownloadResult:
    """Download only audio for a YouTube URL and return its path plus metadata."""

    try:
        from yt_dlp import DownloadError, YoutubeDL
    except ImportError as exc:
        raise AudioDownloadError(
            "Missing Python dependency: yt-dlp. Run `pip install -r requirements.txt`."
        ) from exc

    temp_dir = Path(tempfile.mkdtemp(prefix=TEMP_AUDIO_PREFIX))
    output_template = str(temp_dir / "%(id)s.%(ext)s")
    options: dict[str, Any] = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "128",
            }
        ],
    }

    try:
        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
    except DownloadError as exc:
        message = str(exc)
        if "ffmpeg" in message.lower():
            raise AudioDownloadError(
                "ffmpeg is required but was not found. Install ffmpeg and try again."
            ) from exc
        raise AudioDownloadError(
            "Could not download audio. Check the YouTube URL and your internet connection."
        ) from exc
    except Exception as exc:
        raise AudioDownloadError(f"Unexpected yt-dlp error: {exc}") from exc

    if not info:
        raise AudioDownloadError("yt-dlp did not return video metadata.")

    video_id = _safe_id(info.get("id"))
    audio_path = temp_dir / f"{video_id}.mp3"
    if not audio_path.exists():
        downloaded_files = list(temp_dir.glob("*"))
        if not downloaded_files:
            raise AudioDownloadError("Audio download completed, but no audio file was found.")
        audio_path = downloaded_files[0]

    metadata: VideoMetadata = {
        "title": str(info.get("title") or video_id),
        "video_id": video_id,
        "url": youtube_url,
        "duration": info.get("duration"),
    }
    return {"audio_path": audio_path, "metadata": metadata}
