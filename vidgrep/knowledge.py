
"""
This module handles the core logic of extracting knowledge from a transcription.

It uses a multi-pass LLM approach to generate a concise summary and a list of
main points from a given transcript file. The process is configurable via
the `config/llm_config.json` file.
"""
import sys
import json
import os
from typing import Dict, List, Any
from .llm import call_llm, count_tokens, get_default_model_info, get_default_model
from .transcribe import TranscriptionResult
from langfuse import observe

def load_llm_config() -> Dict[str, Any]:
    """Loads the LLM configuration from the `config/llm_config.json` file."""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'llm_config.json')
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: llm_config.json not found in config/ directory.", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print("Error: llm_config.json is not valid JSON.", file=sys.stderr)
        sys.exit(1)

LLM_CONFIG = load_llm_config()
PROMPTS = LLM_CONFIG['prompts']


@observe()
def load_transcript(file_path: str) -> TranscriptionResult:
    """
    Loads a transcription from a .json or .txt file.

    Args:
        file_path: The absolute path to the transcript file.

    Returns:
        A TranscriptionResult object.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Transcript file not found: {file_path}")
    
    if file_path.endswith('.txt'):
        with open(file_path, 'r') as f:
            content = f.read().strip()
            # A simple parser for plain text or TranscriptionResult string representation
            if content.startswith('TranscriptionResult('):
                text_start = content.find('text=') + 5
                segments_start = content.find('segments=')
                text_part = content[text_start:segments_start-1]
                return TranscriptionResult(text=text_part, segments=[])
            else:
                return TranscriptionResult(text=content, segments=[])
    else:
        with open(file_path, 'r') as f:
            data = json.load(f)
            return TranscriptionResult(
                text=data.get('text', ''),
                segments=data.get('segments', []),
                metadata=data.get('metadata', {})
            )

@observe()
def chunk_transcript(transcript: str, max_tokens: int, overlap_ratio: float = 0.25) -> List[str]:
    """
    Splits a long transcript into overlapping chunks to fit within the LLM context window.

    Args:
        transcript: The full transcript text.
        max_tokens: The maximum number of tokens allowed per chunk.
        overlap_ratio: The percentage of overlap between consecutive chunks.

    Returns:
        A list of transcript chunks.
    """
    model = get_default_model()
    total_tokens = count_tokens(transcript, model)
    
    if total_tokens <= max_tokens:
        return [transcript]
    
    sentences = transcript.split('. ')
    chunks = []
    current_chunk = ""
    
    overlap_tokens = int(max_tokens * overlap_ratio)
    
    for sentence in sentences:
        test_chunk = current_chunk + sentence + ". "
        
        if count_tokens(test_chunk, model) > max_tokens:
            if current_chunk:
                chunks.append(current_chunk.strip())
                words = current_chunk.split()
                overlap_words = words[-overlap_tokens:] if len(words) > overlap_tokens else words
                current_chunk = " ".join(overlap_words) + " " + sentence + ". "
            else:
                chunks.append(sentence + ". ")
                current_chunk = ""
        else:
            current_chunk = test_chunk
    
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks

@observe()
def summarize_text(transcript: str) -> str:
    """
    Generates a summary of the transcript, handling both short and long texts.

    For long transcripts, it uses a multi-pass, map-reduce style summarization.

    Args:
        transcript: The transcript text to summarize.

    Returns:
        A string containing the summary.
    """
    model = get_default_model()
    model_info = get_default_model_info()
    max_input_tokens = model_info['context_window'] - LLM_CONFIG['params']['max_summary_tokens']
    
    transcript_tokens = count_tokens(transcript, model)
    
    if transcript_tokens <= max_input_tokens:
        prompt = PROMPTS["single_pass_summary"].format(transcript=transcript)
        return call_llm(prompt, model, max_tokens=LLM_CONFIG['params']['max_summary_tokens'])
    else:
        chunks = chunk_transcript(transcript, max_input_tokens)
        chunk_summaries = []
        previous_summary = ""
        
        for i, chunk in enumerate(chunks):
            print(f"Summarizing chunk {i+1}/{len(chunks)}...")
            prompt = PROMPTS["chunk_summary_with_context"].format(previous_summary=previous_summary, chunk=chunk) if i > 0 else PROMPTS["chunk_summary"].format(chunk=chunk)
            summary = call_llm(prompt, model, max_tokens=LLM_CONFIG['params']['chunk_summary_max_tokens'])
            chunk_summaries.append(summary)
            previous_summary = summary
        
        combined_summaries = "\n\n".join([f"Section {i+1}: {summary}" for i, summary in enumerate(chunk_summaries)])
        final_prompt = PROMPTS["final_summary"].format(combined_summaries=combined_summaries)
        return call_llm(final_prompt, model, max_tokens=LLM_CONFIG['params']['max_summary_tokens'])

@observe()
def extract_main_points(transcript: str) -> List[str]:
    """
    Extracts a list of main points from the transcript.

    This uses a two-step process: first, generate a bulleted list of points,
    then use a second LLM call to format them into a clean JSON array.

    Args:
        transcript: The transcript text.

    Returns:
        A list of strings, where each string is a main point.
    """
    large_model = get_default_model()
    model_info = get_default_model_info()
    max_input_tokens = model_info['context_window'] - LLM_CONFIG['params']['max_summary_tokens']

    source_text = summarize_text(transcript) if count_tokens(transcript, large_model) > max_input_tokens else transcript

    prompt_text = PROMPTS["extract_main_points_text"].format(source_text=source_text)
    bullet_points_text = call_llm(prompt_text, large_model, max_tokens=LLM_CONFIG['params']['extract_main_points_max_tokens'])

    formatter_model = LLM_CONFIG['models']['formatter']
    prompt_json = PROMPTS["format_as_json_array"].format(bullet_points=bullet_points_text)
    json_response = call_llm(prompt_json, model=formatter_model, max_tokens=LLM_CONFIG['params']['format_as_json_max_tokens'])

    try:
        cleaned_response = json_response.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:-4].strip()
        main_points = json.loads(cleaned_response)
        if isinstance(main_points, list):
            return main_points
    except json.JSONDecodeError:
        print("Warning: Failed to parse JSON. Falling back to line splitting.", file=sys.stderr)
        lines = [line.strip() for line in bullet_points_text.split('\n') if line.strip()]
        return [line.lstrip('- ').lstrip('* ').lstrip('• ') for line in lines if line]

    return []

@observe()
def process_transcript(file_path: str) -> Dict[str, Any]:
    """
    Orchestrates the knowledge extraction process for a single transcript file.

    Args:
        file_path: The path to the transcript file.

    Returns:
        A dictionary containing the 'summary' and 'main_points'.
    """
    print(f"Loading transcript from {file_path}...")
    transcript_result = load_transcript(file_path)
    
    print("Generating summary...")
    summary = summarize_text(transcript_result.text)
    
    print("Extracting main points...")
    main_points = extract_main_points(transcript_result.text)
    
    return {
        "summary": summary,
        "main_points": main_points
    }

@observe()
def main():
    """The main entry point for the script."""
    if len(sys.argv) != 2:
        print(f"Usage: python -m vidgrep.knowledge <transcript_file>", file=sys.stderr)
        print("  transcript_file: Path to transcript file (.json)", file=sys.stderr)
        sys.exit(1)
    
    input_file = sys.argv[1]
    base_name = os.path.splitext(input_file)[0]
    output_file = f"{base_name}.summary.json"
    
    try:
        result = process_transcript(input_file)
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"✅ Knowledge extraction completed!")
        print(f"Summary and main points saved to: {output_file}")
    except Exception as e:
        print(f"❌ Error processing transcript: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
