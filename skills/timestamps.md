---
name: timestamps
description: >
  How to generate YouTube chapter timestamps from a completed video-use EDL.
  Run this after the edit is locked and edl.json exists.
---

# Timestamps Skill

Generates a YouTube-style chapter timestamp structure by reading the `beat`
labels from the EDL. Each unique `beat` value becomes one chapter.

## Prerequisites

- `edit/edl.json` must exist (produced by the video-use editing pipeline)
- EDL `ranges` must have `beat` field set per segment (e.g. "HOOK", "PROBLEM", "SOLUTION")

## Quick Command

```bash
python -m modules.timestamps generate \
    --edit-dir /path/to/footage/edit/
```

Output saved to `edit/timestamps.txt`. Also printed to stdout.

## Output Formats

```bash
# Default YouTube format
python -m modules.timestamps generate --edit-dir <path> --style youtube
# 0:00 Introduction
# 0:45 The Problem
# 2:10 The Solution
# ...

# With "Chapters:" header (for YouTube description sections)
python -m modules.timestamps generate --edit-dir <path> --style chapters

# Minimal (time + label, no decoration)
python -m modules.timestamps generate --edit-dir <path> --style minimal
```

## Python API

```python
from modules.timestamps import generate_timestamps

timestamps_text = generate_timestamps(
    edit_dir="/path/to/footage/edit/",
    style="youtube",      # "youtube" | "chapters" | "minimal"
    include_first_zero=True,  # ensure first chapter always at 0:00
)
print(timestamps_text)
# → saved to edit/timestamps.txt automatically
```

## Beat Label → Chapter Name Mapping

Default mappings (override with `label_map` parameter or custom dict):

| Beat Label | Chapter Name |
|---|---|
| HOOK | Introduction |
| PROBLEM | The Problem |
| SOLUTION | The Solution |
| BENEFIT | Key Benefits |
| EXAMPLE | Live Example |
| DEMO | Demo |
| CTA | Outro |
| INTRO | Introduction |
| SETUP | Setup |
| STEPS | Step-by-Step |
| TUTORIAL | Tutorial |
| RECAP | Recap |
| CONCLUSION | Conclusion |

**Custom chapter names:**
```python
from modules.timestamps import generate_timestamps

timestamps_text = generate_timestamps(
    edit_dir=edit_dir,
    label_map={
        "HOOK": "What Is This About?",
        "PROBLEM": "The Core Problem",
        "SOLUTION": "How We Solved It",
        "CTA": "Let's Stay Connected",
    }
)
```

## How It Works

The generator reads each `ranges` entry from the EDL, calculates the cumulative
output-timeline offset (sum of prior segment durations), and groups consecutive
segments with the same beat into one chapter entry.

Example EDL mapping:
```
HOOK  (C0103: 2.42–6.85)  →  duration 4.43s  →  offset 0:00
HOOK  (C0108: 0.5–3.0)    →  duration 2.5s   →  (same beat, merged)
PROBLEM (C0104: ...)       →  new beat        →  offset 0:06
```
→ `0:00 Introduction`, `0:06 The Problem` ...

## Combining with Description

The caption generator accepts the timestamps string directly:
```python
from modules.timestamps import generate_timestamps
from modules.captions import generate_description, load_style_profile

timestamps = generate_timestamps(edit_dir)
profile = load_style_profile(edit_dir)
desc = generate_description(transcript, profile, include_timestamps=timestamps)
```
