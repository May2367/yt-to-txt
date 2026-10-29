# YouTube Transcriber

A small local command-line tool that downloads audio from a YouTube video and creates a timestamped English transcript. Great for when you want to consume media off youtube but don't feel like watching the whole thing. Now you can just skim the transcript!

## Setup

Install `ffmpeg` separately as a system dependency. `yt-dlp` uses it to extract audio, and Whisper uses it to read audio files.

On Debian/Ubuntu:

```bash
sudo apt-get install ffmpeg
```

## Usage

```bash
python3 main.py "https://youtube.com/watch?v=..."
```

The default Whisper model is `base`. Use `--model tiny` for faster, less accurate CPU tests, or keep `base` for better quality:

```bash
python3 main.py --model tiny "https://youtube.com/watch?v=..."
python3 main.py --model base "https://youtube.com/watch?v=..."
```

## Output

Transcripts are saved under `transcripts/` using the YouTube video ID:

```text
transcripts/
├── dQw4w9WgXcQ.txt
└── dQw4w9WgXcQ.json
```

Transcript lines use a stable format intended for later querying:

```text
[00:00:00] Welcome back to the channel, today we're talking about...
[00:00:04] Let's start with the first topic...
```

The JSON sidecar stores `title`, `video_id`, `url`, `duration`, `transcript_file`, `whisper_model_used`, and `date_transcribed`.

## Future Query Feature

AI querying should plug in as a new `query.py` module that reads the saved `.txt` transcript and matching `.json` metadata, accepts a natural-language question, and sends the transcript plus question to an LLM API. The current transcript format and video-ID naming convention are kept simple so that feature can be added without changing the download/transcribe/save pipeline.
