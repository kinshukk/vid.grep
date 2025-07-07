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
