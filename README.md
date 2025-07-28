# vid.grep

`vid.grep` is a command-line tool to extract knowledge from long videos. It takes a YouTube URL, downloads the audio, transcribes it locally, and then uses a multi-pass LLM process to generate a concise summary and a list of main points.

The core philosophy is to optimize for the "time from video file to actionable insights."

## Usage

```bash
# Run the full pipeline (download, transcribe, summarize)
./scripts/pipeline.sh "<youtube_url>"
```

This will produce two files in the `storage/` directory:
- `<video_title>.json`: The full transcript with word-level timestamps.
- `<video_title>.summary.json`: The summary and main points.
