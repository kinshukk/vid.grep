# GEMINI.md

This file provides guidance to Gemini when working with code in this repository.

## Project Overview

vid.grep is a tool for deep analysis of long videos by searching and navigating their content efficiently. The project uses a multi-pass LLM processing approach to extract knowledge from video content, starting with a detailed transcription. The core philosophy is to optimize for the "time from video file to actionable insights."

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
python transcribe.py <audio_file_path> [device]  # device can be "cpu" or "mlx"
```

## Architecture & Key Design Decisions

### Processing Pipeline
The system is designed as a simple, bash-orchestrated pipeline. Each step is an independent, runnable script that communicates via JSON files.

1.  **Transcription**: `transcribe.sh` and `transcribe.py` use `yt-dlp` to download audio and a local Whisper model (MLX for Apple Silicon, faster-whisper for CPU) to generate transcripts with word-level timestamps.
2.  **Knowledge Extraction**: `extract_knowledge.py` will process the transcript to identify main points and topics using multiple focused LLM calls.
3.  **Verification**: (Planned) `verify_claims.py` will perform external validation of claims made in the video.
4.  **Interface Generation**: (Planned) `generate_interface.py` will create a self-contained, static HTML file for exploring the video content.

### Key Technical Choices
- **Static HTML Output**: For portability and zero deployment complexity.
- **Word-Level Timestamps**: To enable precise navigation and analysis.
- **Multi-Pass LLM Processing**: To improve the quality of extracted knowledge by using focused prompts.
- **JSON Intermediate Format**: For human-readable debugging and simple data exchange between pipeline steps.
- **Direct API Calls**: LLM integration (via OpenRouter) is done with direct API calls to avoid framework abstractions.
- **Fail-Fast Philosophy**: Each step is designed to fail quickly with clear errors, producing inspectable output to aid debugging.

### Storage Structure
- `storage/`: Contains all persistent data.
- Audio files: `storage/<sanitized_video_title>.wav`
- Transcripts: `storage/<sanitized_video_title>.json`

## Script Specifications

### `pipeline.sh`
- **Purpose**: Orchestrates the video processing pipeline, from transcription to knowledge extraction.
- **Input**: YouTube URL (string).
- **Output**: Creates a `<video_title>.out.txt` file in the `storage/` directory containing the extracted knowledge.

### `transcribe.sh`
- **Purpose**: Downloads audio from a YouTube URL, transcribes it using `transcribe.py`, and saves the result as a JSON file.
- **Input**: YouTube URL (string).
- **Output**: Creates a `<video_title>.json` file in the `storage/` directory.

### `transcribe.py`
- **Purpose**: Transcribes an audio file and outputs the transcription result in JSON format.
- **Input**: 
  - `input_filepath` (string): Path to the audio file.
  - `device` (string, optional): The device to use for transcription ("cpu" or "mlx"). Defaults to "cpu".
- **Output**: Prints a JSON object to standard output representing the transcription, including the text, segments with timestamps, and metadata.

### `extract_knowledge.py`
- **Purpose**: Processes a transcript file to extract a summary and main points.
- **Input**: Path to a JSON transcript file (string).
- **Output**: Creates a `<transcript_filename>.summary.json` file.

### `llm.py`
- **Purpose**: Provides a simple, configured interface for making API calls to LLMs via OpenRouter. It is integrated with Langfuse for logging.
- **`call_llm()`**: The primary function for making LLM calls. It takes a user prompt and optional parameters. It is decorated with `@langfuse_logging` to automatically handle logging.
- **Configuration**: All model and API configurations are managed via environment variables, defined in `.env.example`.

### `decorators.py`
- **Purpose**: Contains decorators for cross-cutting concerns, such as logging.
- **`@langfuse_logging`**: A decorator that wraps a function to log its execution to Langfuse, including inputs, outputs, and errors.

## Development Guidelines

When modifying the codebase or adding features, adhere to the following principles:
- **Follow Existing Patterns**: Use bash scripts for orchestration, JSON for intermediate data, and create simple, single-responsibility Python scripts.
- **Independent Steps**: Ensure each part of the pipeline can be run independently.
- **Fail Fast**: Implement clear error handling and logging.
- **The Prime Directive**: Every change should aim to reduce the time it takes to get from a video file to actionable insights. Avoid adding features that do not directly support this goal for v1.

## Misc. Notes
- Consider using SponsorBlock to trim irrelevant sections (ads, sponsor notes) from videos. It uses a crowdsourced database. This may not work for all videos but is a potential enhancement.

## Critical Instructions

### Maintain `LOG.md`
- **Purpose**: To maintain a comprehensive, append-only log of all project activities.
- **Content**: Document all changes, bugs, fixes, style guides, recommendations, experiments, and decisions in `LOG.md`.
- **Format**: Use concise bullet points.
- **Trigger**: Any significant action, such as adding a feature, fixing a bug, or establishing a new convention, must be logged.