---
name: thumbnails
description: >
  How to extract the best frame from a video and generate a thumbnail.
  Two paths: fast PIL compositing, or high-quality HyperFrames HTML rendering.
---

# Thumbnails Skill

Generate YouTube thumbnails from the final edited video. Two paths available:
- **PIL path** (fast, local, no Node required) — frame + text overlay via Pillow
- **HyperFrames path** (high quality, HTML-based) — template renderer via Node

## Quick Command

```bash
python -m modules.thumbnails generate \
    --video /path/to/footage/edit/final.mp4 \
    --edit-dir /path/to/footage/edit/ \
    --title "My Video Title" \
    --subtitle "A Short Description" \
    --method pil
```

Output saved to `edit/thumbnail.png`.

## HyperFrames Method

```bash
python -m modules.thumbnails generate \
    --video edit/final.mp4 \
    --edit-dir edit/ \
    --title "My Video Title" \
    --method hyperframes \
    --template templates/title-card.html
```

Requires Node >= 22 and `npm install` in workspace root.

## Python API

```python
from modules.thumbnails import extractor, composer

# Step 1 — Extract candidate frames from the video at key timestamps
frames = extractor.extract_candidate_frames(
    video_path="/path/to/final.mp4",
    timestamps=[5.0, 30.0, 60.0, 90.0],
    output_dir="/path/to/edit/verify/",
    width=1280,
    height=720,
)

# Or extract from EDL segment midpoints (recommended)
frames = extractor.frames_from_edl(
    video_path="/path/to/final.mp4",
    edl_path="/path/to/edit/edl.json",
    output_dir="/path/to/edit/verify/",
    n_per_beat=1,   # one frame per chapter segment
)

# Step 2 — Pick the sharpest frame
best = extractor.pick_best_frame(frames, criteria="sharpness")

# Step 3a — PIL compositor (fast)
thumbnail = composer.compose_thumbnail_pil(
    base_frame=best,
    title="My Video Title",
    subtitle="Optional subtitle text",
    output_path="/path/to/edit/thumbnail.png",
    style={
        "bg_gradient": True,          # dark gradient behind text
        "text_color": (255, 255, 255),
        "accent_color": (255, 90, 0), # orange bar
        "title_size": 72,             # pt
        "subtitle_size": 42,
        "margin": 60,                 # px from edge
    },
)

# Step 3b — HyperFrames compositor (high quality)
thumbnail = composer.compose_thumbnail_hyperframes(
    base_frame=best,
    template="templates/title-card.html",
    vars={
        "title": "My Video Title",
        "subtitle": "Optional subtitle",
        "accent-color": "#FF5A00",
        "bg-color": "#0A0A0A",
    },
    output_path="/path/to/edit/thumbnail.png",
)
```

## Choosing Between Methods

| | PIL | HyperFrames |
|---|---|---|
| Speed | Fast (~1s) | Slower (~5–10s) |
| Quality | Good | Excellent |
| Requirements | Pillow, numpy | Node >= 22, `npm install` |
| Customisation | Python dict | Full HTML/CSS/JS |
| Best for | Quick drafts, simple text overlay | Final thumbnails, brand-consistent designs |

## Style Tips for High-Converting Thumbnails

- **Font size**: title text at 72pt+ (readable at 240px thumbnail width)
- **Contrast**: always use the dark gradient behind text (`bg_gradient: True`)
- **One element**: don't overcrowd. Title only, or title + 2-word subtitle max.
- **Accent color**: use your brand color for the vertical bar or background highlight
- **Emotion**: the best frame often has the presenter mid-speech with an expressive face

## Deciding the Right Timestamp

For talking-head videos: sample multiple frames in the first 30 seconds (presenter is usually looking at camera and well-lit).
For tutorial/demo videos: pick the moment showing the finished result or the "wow" frame.
For montages: pick the most visually striking frame regardless of narrative position.

Use `extractor.pick_best_frame()` with `criteria="sharpness"` as a starting point,
then swap to a different candidate if the sharpest frame isn't the best visually.
