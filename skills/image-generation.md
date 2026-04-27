---
name: image-generation
description: >
  Documentation on how to generate AI images for thumbnails and motion graphics.
---

# Skill: Image Generation

The workspace includes a unified image generation module that supports both OpenAI's `gpt-image-1` / `dall-e-3` and Google's `Gemini Imagen 3`.

Images can be generated standalone, or directly inside the `thumbnails` and `motion_graphics` pipelines to create AI backgrounds.

## Supported Backends

| Backend | Default Model | Sizes supported automatically |
|---|---|---|
| `openai` | `gpt-image-1` | `1024x1024`, `1792x1024` (landscape), `1024x1792` (portrait) |
| `gemini` | `imagen-3.0-generate-002` | Mapped to aspect ratios: 1:1, 16:9, 9:16 |

*The `auto` backend will use whatever API key is available in `.env`.*

## Style Presets

When generating an image, you can pass a `style` parameter which prepends a crafted text prefix to your prompt:

- `cinematic` — Dramatic lighting, 8k, film grain
- `thumbnail` — Vibrant YouTube style, high contrast
- `motion_bg` — Dark abstract textures, no text, good for backgrounds
- `flat_dark` — Minimal 2D geometry on dark background
- `neon` — Cyberpunk glow, light streaks
- `realistic` — High detail professional photo

## 1. Standalone API

```python
from modules.images import generate_image

paths = generate_image(
    prompt="A glowing server rack in a dark room",
    backend="openai",        # "openai" | "gemini" | "auto"
    size="1792x1024",        # landscape
    quality="hd",            # standard | hd
    style_hint="cinematic",  # style preset
    output_dir="edit/assets/", 
    n=1
)
print("Saved UI to:", paths[0])
```

## 2. Generate an AI Background Thumbnail (No Video Frame Needed)

If the user wants a YouTube thumbnail but the video frames are boring, generate an AI background and slap the title on top:

```python
from modules.thumbnails.composer import compose_thumbnail_ai_bg

path = compose_thumbnail_ai_bg(
    prompt="A developer drinking coffee looking at glowing code",
    title="How I Built This Workspace",
    subtitle="AI Coding in 2026",
    backend="auto",
    style="thumbnail",
    output_path="edit/thumbnail.png"
)
```

## 3. Generate an AI Background for Motion Graphics

If you're rendering a title card or end screen, you can use an AI background instead of a solid color (`data-bg-color`). Wait 10-15 seconds for generation + MP4 render:

```python
from modules.motion_graphics.bridge import render_template_with_ai_bg

path = render_template_with_ai_bg(
    template_path="templates/title-card.html",
    vars={"title": "System Architecture", "subtitle": "Deep Dive"},
    output_mp4="edit/animations/slot_tc1/render.mp4",
    duration=5.0,
    bg_prompt="abstract glowing neural network node map",
    bg_backend="auto",
    bg_style="motion_bg"     # Dark abstract texture without text
)
```

## CLI Usage

```bash
# Check status of available backends
python -m modules.images status

# List all style presets
python -m modules.images styles

# Generate a thumbnail background
python -m modules.images thumbnail-bg \
  --prompt "cyberpunk futuristic city at night" \
  --edit-dir "edit/" \
  --title "The Future is Now"
```
