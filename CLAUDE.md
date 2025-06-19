# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

vid.grep is a tool for diving deep into long videos, searching and skipping to the good parts. The project uses a multi-pass LLM processing approach to extract knowledge from video content through transcription and analysis.

## Commands

### Setup
```bash
# Install dependencies using Poetry
poetry install
```

### Transcription
```bash
# Transcribe a YouTube video (downloads audio and transcribes)
./transcribe.sh "<youtube_url>"

# Transcribe an existing audio file
python transcribe.py <audio_file_path> [device]  # device: "cpu" or "mlx"
```

## Architecture & Key Design Decisions

### Processing Pipeline
The system follows a simple bash-orchestrated pipeline (as outlined in PROJECT_PLAN.md):
1. **Transcription**: Uses Whisper (mlx-whisper for Apple Silicon, faster-whisper for CPU)
2. **Knowledge Extraction**: Multi-pass LLM processing (planned)
3. **Verification**: Optional claim verification (planned)
4. **Interface Generation**: Static HTML output (planned)

### Current Implementation Status
- ✅ Audio download from YouTube (yt-dlp)
- ✅ Transcription with word-level timestamps (mlx/CPU backends)
- ⏳ Knowledge extraction pipeline
- ⏳ LLM integration for analysis
- ⏳ HTML interface generation

### Storage Structure
- `storage/`: Contains downloaded audio files and transcription outputs
- Audio files: `storage/<sanitized_video_title>.wav`
- Transcripts: `storage/<sanitized_video_title>.txt`

### Key Technical Choices
1. **Static HTML Output**: Self-contained files for zero deployment complexity
2. **Word-Level Timestamps**: Maximum precision for navigation
3. **JSON Intermediate Format**: Human-readable debugging and LLM compatibility
4. **Direct API Calls**: No framework abstractions for LLM integration
5. **Fail-Fast Philosophy**: Each pipeline step produces inspectable output

### Transcription Backends
- **MLX (Apple Silicon)**: Uses mlx-whisper with whisper-turbo model
- **CPU Fallback**: Uses faster-whisper with INT8 quantization
- Both backends return structured results with segments containing start/end timestamps

## Development Notes

The project follows the "Prime Directive": Every design choice optimizes for time from video file to actionable insights. Features that don't directly reduce this time don't belong in v1.

When implementing new features, follow the existing patterns:
- Use bash scripts for orchestration
- Output JSON for intermediate data
- Fail fast with clear error messages
- Each step should be independently runnable