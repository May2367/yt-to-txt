"""Transcript formatting and persistence helpers."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from config import OUTPUT_DIR, WHISPER_MODEL
from downloader import VideoMetadata
from transcriber import TranscriptSegment


def format_timestamp(seconds: float) -> str:
    """Convert seconds to HH:MM:SS."""

    total_seconds = max(0, int(seconds))
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def format_transcript(segments: list[TranscriptSegment]) -> str:
    """Return the stable transcript text format used by future query features."""

    lines = [
        f"[{format_timestamp(segment['start'])}] {segment['text']}"
        for segment in segments
        if segment["text"]
    ]
    return "\n".join(lines) + ("\n" if lines else "")


def save_transcript(
    segments: list[TranscriptSegment],
    metadata: VideoMetadata,
    output_dir: str = OUTPUT_DIR,
    model_name: str = WHISPER_MODEL,
) -> tuple[Path, Path]:
    """Save transcript text and JSON sidecar metadata keyed by video ID."""

    transcript_dir = Path(output_dir)
    transcript_dir.mkdir(parents=True, exist_ok=True)

    base_name = metadata["video_id"]
    transcript_path = transcript_dir / f"{base_name}.txt"
    metadata_path = transcript_dir / f"{base_name}.json"

    transcript_path.write_text(format_transcript(segments), encoding="utf-8")
    sidecar = {
        "title": metadata["title"],
        "video_id": metadata["video_id"],
        "url": metadata["url"],
        "duration": metadata["duration"],
        "transcript_file": str(transcript_path),
        "whisper_model_used": model_name,
        "date_transcribed": datetime.now(timezone.utc).isoformat(),
    }
    metadata_path.write_text(json.dumps(sidecar, indent=2) + "\n", encoding="utf-8")
    return transcript_path, metadata_path
