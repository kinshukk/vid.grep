import json

class TranscriptionResult:
    def __init__(self, text: str, segments: list, metadata: dict = None):
        self.text = text
        self.segments = segments
        self.metadata = metadata if metadata is not None else {}

    def __repr__(self):
        return f"TranscriptionResult(text={self.text}\nsegments={self.segments})"

    def to_dict(self):
        return {
            "text": self.text,
            "segments": self.segments,
            "metadata": self.metadata,
        }

def transcribe(input_filepath:str, device:str="mlx", beam_size:int=5):
    if device == "mlx":
        import mlx_whisper

        result = mlx_whisper.transcribe(input_filepath, path_or_hf_repo="mlx-community/whisper-turbo")
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
        model = WhisperModel(model_size_or_path="turbo", device="cpu", compute_type="int8")

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
        print("Usage: python transcribe.py <input_filepath> [device]", file=sys.stderr)
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