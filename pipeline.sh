#!/bin/bash

set -e

# Check if a URL is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <youtube_url>"
  exit 1
fi

YOUTUBE_URL="$1"

# Step 1: Transcribe the video
# This will download the audio and create a .json transcript in the storage/ directory
TRANSCRIPT_FILE=$(./transcribe.sh "$YOUTUBE_URL" | tail -n 1)

if [ -z "$TRANSCRIPT_FILE" ] || [ ! -f "$TRANSCRIPT_FILE" ]; then
  echo "Error: Transcription failed or transcript file not found."
  exit 1
fi

# Step 2: Extract knowledge from the transcript
(cd "$(dirname "$0")" && SCRIPT_DIR=$(dirname "$0")
export PYTHONPATH=$SCRIPT_DIR:$PYTHONPATH
OPENROUTER_API_KEY=$OPENROUTER_API_KEY poetry run python -m extract_knowledge "$TRANSCRIPT_FILE")

SUMMARY_FILE="${TRANSCRIPT_FILE%.json}.summary.json"

if [ -f "$SUMMARY_FILE" ]; then
  echo "Pipeline complete. Output written to $SUMMARY_FILE"
else
  echo "Error: Summary file not found."
  exit 1
fi
