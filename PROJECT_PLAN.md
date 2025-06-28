# Video Research Tool - Design Choices & System Design

## Core Design Philosophy
**Build for immediate utility, not future scale**. Every choice optimizes for getting working output TODAY, with the ability to iterate based on actual usage patterns.

## Critical Design Decisions

### 1. Static HTML Output vs. Web Application
**Choice**: Generate self-contained HTML files

**Rationale**:
- Zero deployment complexity
- Works offline once generated
- Can email/share files directly
- No server maintenance
- Browser is the runtime (free compute)

**Trade-off**: No dynamic updates, but gain simplicity and portability

### 2. Word-Level Timestamps vs. Sentence-Level
**Choice**: Capture word-level timestamps, aggregate to semantic chunks

**Rationale**:
- Precise navigation to exact moments
- Can dynamically adjust granularity later
- Storage is cheap, precision is valuable
- Enables "highlight reel" generation

**Trade-off**: Larger transcript files, but maximum flexibility

### 3. Three-Pass LLM Processing vs. Single Pass
**Choice**: Multiple focused LLM calls

**Rationale**:
```
Pass 1: Main points extraction (wide view)
Pass 2: Deep dive per point (focused context)
Pass 3: Verification queries (external validation)
```

- Better results with focused prompts
- Can use different models per pass (cost optimization)
- Easier to debug and iterate on specific steps
- Natural checkpoints for human review

**Trade-off**: More API calls, but significantly better output quality

### 4. JSON as Intermediate Format
**Choice**: JSON for all intermediate data

**Rationale**:
- Human-readable for debugging
- Easy manipulation with `jq`
- Direct LLM output format
- Simple Python/JavaScript interop
- Can version control knowledge extracts

**Trade-off**: Larger files than binary formats, but worth it for transparency

### 5. Client-Side Video Playback
**Choice**: Embed video file path, use browser's native player

**Rationale**:
- No video hosting/streaming complexity
- Works with local files
- Browser handles all codecs
- Free pause/play/seek functionality

**Trade-off**: Large HTML files if video embedded, so we reference local paths

## System Architecture Decisions

### Orchestration Pattern
```bash
#!/bin/bash
# process_video.sh - Dead simple pipeline

VIDEO=$1
BASENAME=$(basename "$VIDEO" .mp4)

# Step 1: Transcribe
python transcribe.py "$VIDEO" > "transcripts/${BASENAME}.json"

# Step 2: Extract knowledge
cat "transcripts/${BASENAME}.json" | \
  python extract_knowledge.py > "knowledge/${BASENAME}_knowledge.json"

# Step 3: Verify claims (optional, can skip for speed)
cat "knowledge/${BASENAME}_knowledge.json" | \
  python verify_claims.py > "knowledge/${BASENAME}_verified.json"

# Step 4: Generate interface
python generate_interface.py \
  --knowledge "knowledge/${BASENAME}_verified.json" \
  --video "$VIDEO" \
  --output "interfaces/${BASENAME}.html"

echo "Done! Open interfaces/${BASENAME}.html"
```

**Why Bash?**
- Visible data flow
- Easy to run individual steps
- Can parallelize with GNU parallel
- Debugging is just `cat` and `grep`

### LLM Integration Strategy

**Choice**: Direct API calls, no framework
- use openrouter exclusively for LLMs
- whisper (using whisper locally) for transcription

**Rationale**:
- No abstraction layers to debug
- Easy to switch providers
- Can log all prompts/responses
- Direct cost tracking

### Error Handling Philosophy

**Choice**: Fail fast, log everything

**Rationale**:
- Personal tool = you're the debugger
- Better to fix root causes than handle edge cases
- Each step produces inspectable output
- Can always rerun from any step

## Data Schema Decisions

### Timestamp Representation
```json
{
  "timestamp": {
    "start": 125.3,  // Seconds as float
    "end": 130.7,
    "text": "moment description"
  }
}
```

**Why seconds as float?**
- Direct compatibility with video players
- Easy arithmetic for merging ranges
- No timezone/parsing complexity

### Hierarchy Representation
```json
{
  "main_points": [
    {
      "id": "point_1",
      "children": ["point_1_1", "point_1_2"],
      "parent": null
    }
  ],
  "point_index": {
    "point_1_1": { /* full point data */ }
  }
}
```

**Why ID references instead of nesting?**
- Easier to traverse programmatically
- Can reference points from multiple parents
- Simpler LLM output format
- Enables graph structure later

## Interface Design Decisions

### Progressive Disclosure Pattern
```
Level 1: Title + One-liner (always visible)
Level 2: Main points (click to expand)
Level 3: Details + timestamps (expand within point)
Level 4: External verification (load on demand)
```

**Rationale**:
- Cognitive load management
- Fast initial page load
- Explore only what interests you
- Natural reading flow

## Performance Optimization Choices

### Lazy Loading External Verification
- Don't verify until user requests
- Cache all search results
- Batch API calls when possible

### Pre-compute Everything Expensive
- All LLM processing happens once
- HTML generation is deterministic
- User interactions are instant

## Future Iteration Points
These are intentionally NOT implemented in v1:
- Multi-video cross-references
- Personal knowledge base integration  
- Real-time re-processing
- Collaborative annotations

**Why exclude these?**
First prove the core loop works. Every feature adds complexity. Ship the critical path, then enhance based on actual usage pain points.

## The Prime Directive
**Every design choice optimizes for one metric: Time from video file to actionable insights**

If a feature doesn't directly reduce this time, it doesn't belong in v1.