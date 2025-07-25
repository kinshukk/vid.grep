#!/bin/bash
set -e

# Ensure the script is run from the project root
if [ ! -f "pyproject.toml" ]; then
  echo "Error: This script must be run from the project root directory." >&2
  exit 1
fi

# Check if a URL is provided
if [ -z "$1" ]; then
  echo "Usage: ./scripts/pipeline.sh <youtube_url>" >&2
  exit 1
fi

URL="$1"
STORAGE_DIR="./storage"

# Create storage directory if it doesn't exist
mkdir -p "$STORAGE_DIR"

# Get video title
echo "Fetching video info..."
TITLE=$(yt-dlp "$URL" --get-title --no-download)
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to fetch video title" >&2
    exit 1
fi

# Sanitize title for filename
SANITIZED_TITLE=$(echo "$TITLE" | sed 's/[<>:"/\\|?*]/_/g' | tr -d '\n\r')
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
SAFE_TITLE="${TIMESTAMP}--${SANITIZED_TITLE}"

AUDIO_FILE="$STORAGE_DIR/${SAFE_TITLE}.wav"
TRANSCRIPT_FILE="$STORAGE_DIR/${SAFE_TITLE}.json"
SUMMARY_FILE="$STORAGE_DIR/${SAFE_TITLE}.summary.json"

# Download audio
echo "Downloading audio..."
yt-dlp "$URL" --extract-audio --audio-format wav -o "$AUDIO_FILE"
if [ $? -ne 0 ]; then
    echo "ERROR: Audio download failed" >&2
    exit 1
fi

# Transcribe audio
echo "Transcribing audio..."
poetry run python -m vidgrep.transcribe "$AUDIO_FILE" > "$TRANSCRIPT_FILE"
if [ $? -ne 0 ]; then
    echo "ERROR: Transcription failed" >&2
    exit 1
fi
echo "SUCCESS: Transcription saved to $TRANSCRIPT_FILE"

# Extract knowledge
echo "Extracting knowledge..."
poetry run python -m vidgrep.knowledge "$TRANSCRIPT_FILE"
if [ $? -ne 0 ]; then
    echo "ERROR: Knowledge extraction failed" >&2
    exit 1
fi

echo "Pipeline complete. Output written to $SUMMARY_FILE"