# Log

This is an append-only log to document all changes, bugs, fixes, style guides, recommendations, things tried, etc. for future reference.

- **`llm.py` Refactoring:**
  - Extracted model details (model name, max output, context window) into `.env.example`.
  - Added `SYSTEM_PROMPT` to `.env.example` and integrated it as the first message in `call_llm`.
  - added reasoning tokens in LLM call in `call_llm`
- **Langfuse Integration:**
  - Added `langfuse` as a dependency.
  - Added Langfuse configuration (`LANGFUSE_HOST`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_PUBLIC_KEY`) to `.env.example`.
  - Created a `decorators.py` file with a `@langfuse_logging` decorator to cleanly handle logging for LLM calls.
  - Applied the decorator to the `call_llm` function in `llm.py` to log inputs, outputs, and errors without cluttering the main logic.
  - custom decorator didn't work due to incompatibility issues with latest langfuse SDK, so reverted to using `@observe()` decorator
- **Configuration and Pipeline Refinements:**
  - Centralized all LLM-related constants (model names, token limits, prompts) into a single `llm_config.json` file, removing `prompts.json`.
  - Refactored `extract_knowledge.py` to load all configuration from `llm_config.json`, eliminating hardcoded values.
  - Improved pipeline robustness by having `transcribe.sh` output the generated filename directly.
  - Updated `pipeline.sh` to use the explicit filename, removing fragile `ls -t` logic.
  - Simplified `llm.py` by clarifying model info functions and making the API endpoint configurable.
- **Code Refactoring and Testing Setup:**
  - Consolidated shell scripts: Merged `transcribe.sh` into `pipeline.sh`.
  - Reorganized file structure: Moved Python files into a `vidgrep/` package, scripts into a `scripts/` directory, and `llm_config.json` into a `config/` directory.
  - Improved documentation: Added docstrings to Python files and updated `README.md` and `GEMINI.md`.
  - Enhanced robustness: Implemented timestamped file naming for output and improved error handling.
  - Created `tests/` directory and `integration_test.py` to test the entire pipeline.
  - Fixed various syntax and import errors during testing.
  - Configured `pytest.ini` for `pythonpath`.
  - Merged `feat/code-refactoring-and-testing` into `master` and deleted the feature branch.