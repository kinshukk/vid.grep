# transcribe.sh
#!/bin/bash

# Check if URL provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <youtube_url>"
    exit 1
fi

URL="$1"
STORAGE_DIR="./storage"

# Create storage directory if it doesn't exist
mkdir -p "$STORAGE_DIR"

# Get video title and download audio
echo "Fetching video info and downloading audio..."
TITLE=$(yt-dlp "$URL" --get-title --no-download)

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to fetch video title"
    exit 1
fi

# Sanitize title for filename (remove problematic chars)
SAFE_TITLE=$(echo "$TITLE" | sed 's/[<>:"/\\|?*]/_/g' | tr -d '\n\r')

# Download audio
yt-dlp "$URL" --extract-audio --audio-format wav --output "$STORAGE_DIR/${SAFE_TITLE}.%(ext)s"

if [ $? -ne 0 ]; then
    echo "ERROR: Audio download failed"
    exit 1
fi

WAV_FILE="$STORAGE_DIR/${SAFE_TITLE}.wav"

# Verify file exists
if [ ! -f "$WAV_FILE" ]; then
    echo "ERROR: WAV file not found at $WAV_FILE"
    exit 1
fi

# Get absolute path
FULL_PATH=$(realpath "$WAV_FILE")

echo "Transcribing audio..."
export OPENROUTER_API_KEY=$OPENROUTER_API_KEY
poetry run python -m transcribe "$FULL_PATH" mlx > "$STORAGE_DIR/${SAFE_TITLE}.json"

if [ $? -eq 0 ]; then
    echo "SUCCESS: Transcription saved to $STORAGE_DIR/${SAFE_TITLE}.txt"
else
    echo "ERROR: Transcription failed"
    exit 1
fi