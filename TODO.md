## Up Next

- [ ] **Progress Bar**: Implement a progress bar for transcription and an overall pipeline progress bar.
- [ ] **Contextual Summarization**: Pass the summary of the previous chunk to the next chunk during chunked summarization to maintain context.
- [ ] **SponsorBlock Integration**: Consider using SponsorBlock to trim irrelevant sections from videos. This uses a crowdsourced database and may not work for all videos but is a potential enhancement.

---

## Future Ideas & Enhancements

- [ ] **Variable Summary Detail**: 
  - Add a parameter for the level of summary detail.
  - Automatically detect the required level of detail based on content (e.g., technical podcast vs. casual vlog).
  - Learn user preferences for summary detail over time.

---

## Completed

- [x] **Improve File Naming Convention**: Updated to `YYYY-MM-DD-hh-mm-ss--<video-title>.<extension>`. (Done in `scripts/pipeline.sh`)
- [x] **Update `pipeline.sh`**: The root `pipeline.sh` has been removed in favor of `scripts/pipeline.sh`.
