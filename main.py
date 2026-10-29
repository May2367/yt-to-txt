"""Command-line entry point for YouTube audio transcription."""

from __future__ import annotations

import argparse
import shutil
import sys
import threading
import time
from pathlib import Path

from config import WHISPER_MODEL
from downloader import AudioDownloadError, download_audio
from formatter import save_transcript
from transcriber import TranscriptionError, transcribe_audio


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download YouTube audio and create a timestamped English transcript."
    )
    parser.add_argument(
        "--model",
        default=WHISPER_MODEL,
        choices=("tiny", "base", "small", "medium", "large"),
        help=f"Whisper model to use. Defaults to {WHISPER_MODEL!r}.",
    )
    parser.add_argument("youtube_url", help="YouTube video URL to transcribe")
    return parser.parse_args()


def format_duration(seconds: int) -> str:
    minutes, secs = divmod(max(0, seconds), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours:d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:d}:{secs:02d}"


def format_file_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"


def cleanup_audio(audio_path: Path) -> None:
    temp_dir = audio_path.parent
    shutil.rmtree(temp_dir, ignore_errors=True)


def start_progress_logger(
    message: str,
    interval_seconds: int = 180,
) -> tuple[threading.Event, threading.Thread]:
    stop_event = threading.Event()

    def log_progress() -> None:
        start = time.monotonic()
        while not stop_event.wait(interval_seconds):
            elapsed = int(time.monotonic() - start)
            print(f"{message} Elapsed: {format_duration(elapsed)}", flush=True)

    thread = threading.Thread(target=log_progress, daemon=True)
    thread.start()
    return stop_event, thread


def main() -> int:
    args = parse_args()
    audio_path: Path | None = None

    try:
        print("Downloading audio with yt-dlp...")
        download = download_audio(args.youtube_url)
        audio_path = download["audio_path"]
        metadata = download["metadata"]
        print(f"Downloaded audio for: {metadata['title']}")
        print(f"Temporary audio file: {audio_path}")
        print(f"Audio size: {format_file_size(audio_path.stat().st_size)}")

        duration = metadata.get("duration")
        if duration is not None:
            print(f"Video duration: {format_duration(duration)}")

        print(
            f"Transcribing with Whisper model {args.model!r}. "
            "CPU transcription can take a while for long videos."
        )
        stop_progress, progress_thread = start_progress_logger("Still transcribing...")
        try:
            segments = transcribe_audio(audio_path, args.model)
        finally:
            stop_progress.set()
            progress_thread.join(timeout=1)
        print(f"Transcribed {len(segments)} segments.")

        print("Saving transcript and metadata...")
        transcript_path, metadata_path = save_transcript(
            segments,
            metadata,
            model_name=args.model,
        )
        print(f"Transcript saved to: {transcript_path}")
        print(f"Metadata saved to: {metadata_path}")
        return 0
    except AudioDownloadError as exc:
        print(f"Download error: {exc}", file=sys.stderr)
        return 1
    except TranscriptionError as exc:
        print(f"Transcription error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130
    finally:
        if audio_path is not None:
            print("Cleaning up temporary audio files...")
            cleanup_audio(audio_path)


if __name__ == "__main__":
    raise SystemExit(main())
