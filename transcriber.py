"""Whisper speech-to-text wrapper."""

from __future__ import annotations

from pathlib import Path
from typing import TypedDict


class TranscriptSegment(TypedDict):
    start: float
    end: float
    text: str


class TranscriptionError(RuntimeError):
    """Raised when Whisper cannot transcribe the audio file."""


def transcribe_audio(audio_path: Path, model_name: str) -> list[TranscriptSegment]:
    """Transcribe audio with local Whisper, forcing English transcription."""

    try:
        import whisper

        model = whisper.load_model(model_name)
        result = model.transcribe(str(audio_path), language="en")
    except ImportError as exc:
        raise TranscriptionError(
            "Missing Python dependency: openai-whisper. Run `pip install --no-deps openai-whisper==20250625`."
        ) from exc
    except FileNotFoundError as exc:
        raise TranscriptionError(
            "Whisper could not read the audio file. Make sure ffmpeg is installed."
        ) from exc
    except Exception as exc:
        raise TranscriptionError(f"Whisper transcription failed: {exc}") from exc

    segments: list[TranscriptSegment] = []
    for segment in result.get("segments", []):
        segments.append(
            {
                "start": float(segment["start"]),
                "end": float(segment["end"]),
                "text": str(segment["text"]).strip(),
            }
        )
    return segments
