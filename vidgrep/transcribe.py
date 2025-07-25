"""
This module provides functions for transcribing audio files using a local Whisper model.

It supports both MLX for Apple Silicon and a faster-whisper CPU fallback,
outputting the transcription result in a structured JSON format.
"""
import json
from typing import List, Dict, Any
from langfuse import observe
from dotenv import load_dotenv
load_dotenv()

class TranscriptionResult:
    """A data class to hold the results of a transcription."""
    def __init__(self, text: str, segments: List[Dict[str, Any]], metadata: Dict[str, Any] = None):
        self.text = text
        self.segments = segments
        self.metadata = metadata if metadata is not None else {}

    def __repr__(self):
        return f"TranscriptionResult(text={self.text}\nsegments={self.segments})"

    def to_dict(self) -> Dict[str, Any]:
        """Converts the TranscriptionResult to a dictionary."""
        return {
            "text": self.text,
            "segments": self.segments,
            "metadata": self.metadata,
        }

@observe()
def transcribe(input_filepath:str, device:str="mlx", beam_size:int=5) -> 'TranscriptionResult':
    """
    Transcribes an audio file using the specified device.

    Args:
        input_filepath: Path to the audio file to transcribe.
        device: The device to use for transcription ("cpu" or "mlx").
        beam_size: The beam size to use for transcription.

    Returns:
        A TranscriptionResult object containing the text, segments, and metadata.
    """
    if device == "mlx":
        import mlx_whisper

        result = mlx_whisper.transcribe(input_filepath, path_or_hf_repo="mlx-community/whisper-large-v3-mlx-4bit")
        return TranscriptionResult(
            text=result["text"],
            segments=result["segments"],
            metadata={
                "language": result["language"],
            }
        )
    else:
        # faster-whisper fallback
        from faster_whisper import WhisperModel
        from tqdm import tqdm

        # cpu, INT8
        model = WhisperModel(model_size_or_path="large-v3", device="cpu", compute_type="int8")

        segments, info = model.transcribe(input_filepath, beam_size=beam_size)
        segs = [s for s in tqdm(segments)] # collecting from generator
        return TranscriptionResult(
            text="".join([segment.text for segment in segs]), # progress bar since cpu takes much longer
            segments=[{
                "start": segment.start,
                "end": segment.end,
                "text": segment.text
            } for segment in segs],
            metadata={
                "language": info.language,
                "language_probability": info.language_probability
            }
        )

if __name__ == "__main__":
    import sys, time
    if len(sys.argv) < 2:
        print("Usage: python -m vidgrep.transcribe <input_filepath> [device]", file=sys.stderr)
        sys.exit(1)
    
    input_filepath = sys.argv[1]
    device = sys.argv[2] if len(sys.argv) > 2 else "cpu"  # "cpu" or "mlx"
    beam_size = 5 # keeping default for now

    print(f"Starting transcription using {device.upper()} backend", file=sys.stderr)
    start_time = time.perf_counter()
    result = transcribe(input_filepath, beam_size=beam_size, device=device)
    end_time = time.perf_counter()
    execution_time = end_time - start_time
    print(f"✅ Transcription completed in {execution_time:.2f}s | backend: ({device.upper()})", file=sys.stderr)
    
    # Output as JSON
    print(json.dumps(result.to_dict(), indent=2))