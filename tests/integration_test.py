
"""
Integration test for the main processing pipeline.
"""
import os
import subprocess
import json
import glob

# --- Test Configuration ---
YOUTUBE_URL = "https://www.youtube.com/watch?v=RYdgtTQAIVs"
STORAGE_DIR = "./storage"

def cleanup_storage():
    """Removes all generated files from the storage directory."""
    print("--- Cleaning up storage directory ---")
    files = glob.glob(os.path.join(STORAGE_DIR, '*'))
    for f in files:
        # Keep .gitignore if it exists
        if os.path.basename(f) != '.gitignore':
            os.remove(f)
    print("Cleanup complete.")

def test_pipeline():
    """Runs the full pipeline and verifies the output."""
    # 1. Cleanup storage before running
    cleanup_storage()

    # 2. Run the pipeline script
    print(f"--- Running pipeline for URL: {YOUTUBE_URL} ---")
    script_path = os.path.abspath("./scripts/pipeline.sh")
    process = subprocess.run(
        [script_path, YOUTUBE_URL],
        capture_output=True,
        text=True,
        cwd=os.path.abspath('.') # Ensure it runs from project root
    )

    # Print stdout and stderr for debugging
    print("--- Pipeline STDOUT ---")
    print(process.stdout)
    print("--- Pipeline STDERR ---")
    print(process.stderr)

    # 3. Assert that the script ran successfully
    assert process.returncode == 0, f"Pipeline script failed with exit code {process.returncode}"

    # 4. Verify that the output files were created
    print("--- Verifying output files ---")
    output_files = os.listdir(STORAGE_DIR)
    
    # Find the files based on the sanitized title prefix
    # Note: This is a bit fragile if the title changes, but good for a first pass.
    base_name_part = "Testing APDS, APFSDS, HE and HEAT.._(or APHE)"
    
    wav_files = [f for f in output_files if base_name_part in f and f.endswith('.wav')]
    transcript_files = [f for f in output_files if base_name_part in f and f.endswith('.json') and not f.endswith('.summary.json')]
    summary_files = [f for f in output_files if base_name_part in f and f.endswith('.summary.json')]

    assert len(wav_files) == 1, f"Expected 1 .wav file, but found {len(wav_files)}"
    assert len(transcript_files) == 1, f"Expected 1 .json transcript file, but found {len(transcript_files)}"
    assert len(summary_files) == 1, f"Expected 1 .summary.json file, but found {len(summary_files)}"

    print("Output files verified.")

    # 5. Verify the content of the summary file
    print("--- Verifying summary file content ---")
    summary_file_path = os.path.join(STORAGE_DIR, summary_files[0])
    with open(summary_file_path, 'r') as f:
        summary_data = json.load(f)

    assert "summary" in summary_data, "Summary key missing from summary.json"
    assert "main_points" in summary_data, "Main points key missing from summary.json"
    assert isinstance(summary_data["summary"], str), "Summary content is not a string"
    assert len(summary_data["summary"]) > 50, "Summary content seems too short"
    assert isinstance(summary_data["main_points"], list), "Main points content is not a list"
    assert len(summary_data["main_points"]) > 0, "Main points list is empty"

    print("Summary file content verified.")
    print("\n✅✅✅ Integration test passed! ✅✅✅")

if __name__ == "__main__":
    test_pipeline()

