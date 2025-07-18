import sys
import json
import os
from typing import Dict, List, Any
from llm import call_llm, count_tokens, get_default_model_info, get_default_model
from transcribe import TranscriptionResult
from langfuse import observe

def load_llm_config() -> Dict[str, Any]:
    """Load LLM config from llm_config.json."""
    try:
        with open("llm_config.json", 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: llm_config.json not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print("Error: llm_config.json is not valid JSON.")
        sys.exit(1)

LLM_CONFIG = load_llm_config()
PROMPTS = LLM_CONFIG['prompts']


@observe()
def load_transcript(file_path: str) -> TranscriptionResult:
    """Load transcript from file path."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Transcript file not found: {file_path}")
    
    # Handle both .txt files from transcribe.py output and direct JSON
    if file_path.endswith('.txt'):
        with open(file_path, 'r') as f:
            content = f.read().strip()
            # Parse the TranscriptionResult output format
            if content.startswith('TranscriptionResult('):
                # Extract text and segments from the string representation
                # This is a simple parser - could be improved
                text_start = content.find('text=') + 5
                segments_start = content.find('segments=')
                text_part = content[text_start:segments_start-1]
                
                # For now, create a simple result with just the text
                return TranscriptionResult(text=text_part, segments=[])
            else:
                # Plain text file
                return TranscriptionResult(text=content, segments=[])
    else:
        # Assume JSON format
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
    Chunk transcript into overlapping segments for long texts.
    
    Args:
        transcript: Full transcript text
        max_tokens: Maximum tokens per chunk
        overlap_ratio: Ratio of overlap between chunks
        
    Returns:
        List of text chunks
    """
    model = get_default_model()
    total_tokens = count_tokens(transcript, model)
    
    if total_tokens <= max_tokens:
        return [transcript]
    
    # Split by sentences to maintain semantic boundaries
    sentences = transcript.split('. ')
    chunks = []
    current_chunk = ""
    
    overlap_tokens = int(max_tokens * overlap_ratio)
    
    for sentence in sentences:
        test_chunk = current_chunk + sentence + ". "
        
        if count_tokens(test_chunk, model) > max_tokens:
            if current_chunk:
                chunks.append(current_chunk.strip())
                
                # Create overlap for next chunk
                words = current_chunk.split()
                overlap_words = words[-overlap_tokens:] if len(words) > overlap_tokens else words
                current_chunk = " ".join(overlap_words) + " " + sentence + ". "
            else:
                # Single sentence is too long, force include it
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
    Generate a summary of the transcript.
    Handles both short and long transcripts.
    """
    model = get_default_model()
    model_info = get_default_model_info()
    max_input_tokens = model_info['context_window'] - LLM_CONFIG['params']['max_summary_tokens']  # Reserve for prompt and output
    
    # Check if transcript fits in single call
    transcript_tokens = count_tokens(transcript, model)
    
    if transcript_tokens <= max_input_tokens:
        # Single pass summarization
        prompt = PROMPTS["single_pass_summary"].format(transcript=transcript)
        
        return call_llm(prompt, model, max_tokens=LLM_CONFIG['params']['max_summary_tokens'])
    
    else:
        # Multi-pass summarization for long transcripts
        chunks = chunk_transcript(transcript, max_input_tokens)
        chunk_summaries = []
        
        for i, chunk in enumerate(chunks):
            print(f"Summarizing chunk {i+1}/{len(chunks)}...")
            
            prompt = PROMPTS["chunk_summary"].format(chunk=chunk)
            
            summary = call_llm(prompt, model, max_tokens=LLM_CONFIG['params']['chunk_summary_max_tokens'])
            chunk_summaries.append(summary)
        
        # Combine chunk summaries into final summary
        combined_summaries = "\n\n".join([f"Section {i+1}: {summary}" for i, summary in enumerate(chunk_summaries)])
        
        final_prompt = PROMPTS["final_summary"].format(combined_summaries=combined_summaries)
        
        return call_llm(final_prompt, model, max_tokens=LLM_CONFIG['params']['max_summary_tokens'])

@observe()
def extract_main_points(transcript: str) -> List[str]:
    """
    Extract main points/topics from the transcript using a two-step process.
    """
    # Step 1: Get main points as bulleted list from the default model
    large_model = get_default_model()
    model_info = get_default_model_info()
    max_input_tokens = model_info['context_window'] - LLM_CONFIG['params']['max_summary_tokens']

    if count_tokens(transcript, large_model) > max_input_tokens:
        source_text = summarize_text(transcript)
    else:
        source_text = transcript

    prompt_text = PROMPTS["extract_main_points_text"].format(source_text=source_text)
    bullet_points_text = call_llm(prompt_text, large_model, max_tokens=LLM_CONFIG['params']['extract_main_points_max_tokens'])

    # Step 2: Format the bullet points into a JSON array using a smaller model
    formatter_model = LLM_CONFIG['models']['formatter']
    prompt_json = PROMPTS["format_as_json_array"].format(bullet_points=bullet_points_text)
    
    json_response = call_llm(prompt_json, model=formatter_model, max_tokens=LLM_CONFIG['params']['format_as_json_max_tokens'])

    try:
        # Clean up the response before parsing
        cleaned_response = json_response.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:-4].strip()
            
        main_points = json.loads(cleaned_response)
        if isinstance(main_points, list):
            return main_points
    except json.JSONDecodeError:
        print("Warning: Failed to parse JSON from formatter model. Falling back to line splitting.")
        # Fallback to parsing the bullet points from the first call
        lines = [line.strip() for line in bullet_points_text.split('\n') if line.strip()]
        return [line.lstrip('- ').lstrip('* ').lstrip('• ') for line in lines if line]

    # Fallback if JSON parsing still fails for some reason
    return []

@observe()
def process_transcript(file_path: str) -> Dict[str, Any]:
    """
    Process a transcript file to extract summary and main points.
    
    Returns:
        Dictionary with 'summary' and 'main_points' keys
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
    if len(sys.argv) != 2:
        print("Usage: python extract_knowledge.py <transcript_file>")
        print("  transcript_file: Path to transcript file (.txt or .json)")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    # Generate output filename
    base_name = os.path.splitext(input_file)[0]
    output_file = f"{base_name}.summary.json"
    
    try:
        result = process_transcript(input_file)
        
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"✅ Knowledge extraction completed!")
        print(f"Summary and main points saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ Error processing transcript: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()