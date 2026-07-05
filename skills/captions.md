---
name: captions
description: >
  How to generate style-matched captions, video descriptions, and titles.
  Supports YouTube, Instagram, LinkedIn, Twitter/X, and TikTok.
---

# Captions & Descriptions Skill

Generate titles, descriptions, and platform captions that match the creator's
writing style. The module learns style from sample texts, caches it in
`edit/style_profile.json`, and uses it for all subsequent generations.

## Prerequisites

- `edit/takes_packed.md` or any transcript text file in `edit/`
- Optional: `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` in `.env`
  (falls back to rule-based generation without a key)

## Step 1 — Set Up (or Verify) a Style Profile

**If the user has never set up a style profile:**

1. Ask: "Can you paste 2-3 examples of your typical captions or video descriptions?"
2. Run:
   ```bash
   python -m modules.captions analyze-style \
       --edit-dir /path/to/footage/edit/ \
       --samples "Example text 1..." "Example text 2..."
   ```
3. This saves `edit/style_profile.json`. Show the user what was inferred and ask if it looks right.

**If `edit/style_profile.json` already exists:** load and use it automatically.

## Step 2 — Generate All Content

```bash
python -m modules.captions generate \
    --edit-dir /path/to/footage/edit/ \
    --platform youtube \
    --n-titles 5
```

This produces:
- `edit/title_options.md` — 5 title candidates
- `edit/description.md` — full YouTube description
- `edit/caption_youtube.md` — short hook caption

If `edit/edl.json` exists, the generator also extracts high-impact hook
candidates from each beat and feeds them to the LLM. This makes titles and
descriptions structurally aligned with the actual edit.

For other platforms:
```bash
python -m modules.captions generate --edit-dir <path> --platform instagram
python -m modules.captions generate --edit-dir <path> --platform linkedin
python -m modules.captions generate --edit-dir <path> --platform twitter
python -m modules.captions generate --edit-dir <path> --platform tiktok
```

## Hook Scoring

`modules/captions/hooks.py` scores transcript lines for title/thumbnail potential:

```python
from modules.captions.hooks import extract_hooks, top_hook_per_beat

hooks = extract_hooks(transcript_text, "/path/to/edit/edl.json", top_n=5)
per_beat = top_hook_per_beat(transcript_text, "/path/to/edit/edl.json")
```

Scoring favors sentences that are 6-12 words, contain numbers, ask questions,
or use strong verbs, and appear early in a chapter.

## Python API

```python
from modules.captions import analyze_style, generate_title_options, generate_description, generate_caption
from modules.captions import load_style_profile, default_profile

# Load cached profile (returns None if none exists)
profile = load_style_profile("/path/to/edit") or default_profile()

# Generate 5 title options
titles = generate_title_options(transcript_text, profile, n=5)

# Full description with timestamps embedded
from modules.timestamps import generate_timestamps
timestamps = generate_timestamps("/path/to/edit")
desc = generate_description(transcript_text, profile, include_timestamps=timestamps)

# Platform-specific caption
cap = generate_caption(transcript_text, profile, platform="instagram")
```

## StyleProfile Fields

| Field | Type | Description |
|---|---|---|
| `tone` | str | conversational, formal, hype, educational, storytelling |
| `avg_sentence_len` | int | Average words per sentence |
| `emoji_usage` | bool | Whether to include emoji |
| `cta_style` | str | How they end captions (e.g. "Subscribe below 👇") |
| `common_phrases` | list[str] | Recurring phrases/vocabulary |
| `hashtags` | dict | Per-platform hashtag lists |
| `creator_name` | str | Creator brand name |
| `niche` | str | Topic area (tech, travel, education, etc.) |

## Manual Style Profile

You can hand-write `edit/style_profile.json` directly:
```json
{
  "tone": "hype",
  "avg_sentence_len": 12,
  "emoji_usage": true,
  "cta_style": "Subscribe for more 🔥",
  "common_phrases": ["let's get it", "no cap", "real talk"],
  "hashtags": {
    "youtube": [],
    "instagram": ["#contentcreator", "#videoproduction"]
  },
  "creator_name": "Khalid",
  "niche": "tech",
  "sample_texts": []
}
```

## Without an LLM Key

The module includes a rule-based fallback that generates basic (but functional)
titles, descriptions, and captions from the transcript alone. Quality improves
significantly with an LLM key — strongly recommended for style matching.
