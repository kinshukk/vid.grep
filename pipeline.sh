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
./transcribe.sh "$YOUTUBE_URL"

# Step 2: Determine the output filename
# The transcribe.sh script creates a file based on the video title.
# We need to find the latest .json file in the storage directory.
TRANSCRIPT_FILE=$(ls -t storage/*.json | head -n 1)

if [ -z "$TRANSCRIPT_FILE" ]; then
  echo "Error: No transcript file found in storage/ directory."
  exit 1
fi

# Step 3: Extract knowledge from the transcript
poetry run python extract_knowledge.py "$TRANSCRIPT_FILE"

# The output of extract_knowledge.py is a .summary.json file.
# We will rename it to <original-filename>.out.txt
SUMMARY_FILE="${TRANSCRIPT_FILE%.json}.summary.json"
OUTPUT_FILE="storage/$(basename "${TRANSCRIPT_FILE%.json}").out.txt"

if [ -f "$SUMMARY_FILE" ]; then
  mv "$SUMMARY_FILE" "$OUTPUT_FILE"
  echo "Pipeline complete. Output written to $OUTPUT_FILE"
else
  echo "Error: Summary file not found."
  exit 1
fi
