---
name: motion-graphics
description: >
  How to create and add animated motion graphics overlays using HyperFrames
  and the Python bridge module. Read this when adding overlays to a video.
---

# Motion Graphics Skill

Motion graphics in this workspace are built as **HTML compositions** and rendered
to MP4 by HyperFrames. They plug directly into the video-use EDL via the `overlays` key.

## Workflow

1. **Choose a template** from `templates/` (or write a custom HTML composition)
2. **Render it** using the Python bridge module — one liner per animation slot
3. **Add to EDL** under `overlays` with `start_in_output` and `duration`
4. **Re-render** with `render.py` — HyperFrames clips are composited with correct PTS shift

## Template Catalog

### `lower-third.html`
Slide-in name plate with accent bar. Ideal for introducing a speaker.
```python
from modules.motion_graphics import bridge

path = bridge.add_lower_third(
    name="Khalid Al-Mansouri",
    title="Product Designer",
    output_dir="/path/to/footage/edit",
    slot_id="lt1",
    duration=4.0,
    accent_color="#FF5A00",
)
```

| Variable | Type | Default |
|---|---|---|
| `name` / `data-title` | string | "Name" |
| `title` / `data-subtitle` | string | "" |
| `accent-color` | hex | #FF5A00 |
| `bg-color` | hex | rgba(10,10,10,0.85) |
| `duration` | float | 4.0s |

---

### `title-card.html`
Full-screen title card with accent line reveal. For intro/outro.
```python
path = bridge.add_title_card(
    title="How We Built This in 48 Hours",
    subtitle="A Behind-the-Scenes Story",
    output_dir=edit_dir,
    slot_id="tc1",
    duration=5.0,
)
```

---

### `chapter-intro.html`
Chapter transition (centered, fade + letter-spacing reveal). 3s recommended.
```python
path = bridge.add_chapter_intro(
    chapter_name="The Problem",
    chapter_number="01",
    output_dir=edit_dir,
    slot_id="ch1",
    duration=3.0,
)
```

---

### `subscribe-bump.html`
Corner subscribe animation. Appears in the lower-right for 3s.
```python
path = bridge.add_subscribe_bump(
    output_dir=edit_dir,
    slot_id="sub1",
    duration=3.0,
    accent_color="#FF0000",
)
```

---

### `end-screen.html`
Full-screen end screen with subscribe button and bell. 15s recommended.
```python
path = bridge.render_template(
    template_path="templates/end-screen.html",
    vars={"title": "My Channel", "subtitle": "New videos every week"},
    output_mp4=f"{edit_dir}/animations/slot_end1/render.mp4",
    duration=15.0,
)
```

## Generic Render Call
Any template can be rendered via the generic function:
```python
from modules.motion_graphics import bridge

path = bridge.render_template(
    template_path="templates/lower-third.html",   # or custom HTML
    vars={
        "title": "Main Text",
        "subtitle": "Secondary Text",
        "accent-color": "#FF5A00",
        "bg-color": "#0A0A0A",
        "font": "Inter",
    },
    output_mp4="/path/to/edit/animations/slot_1/render.mp4",
    duration=4.0,
    fps=30,
    width=1920,
    height=1080,
)
```

## Adding to the EDL

After rendering, add the path to your `edl.json`:
```json
{
  "overlays": [
    {
      "file": "edit/animations/slot_lt1/render.mp4",
      "start_in_output": 5.2,
      "duration": 4.0
    }
  ]
}
```

`start_in_output` is the output-timeline second at which the overlay appears.
Overlays are applied BEFORE subtitles (enforced by Hard Rule 1 in video-use SKILL.md).

## Parallel Sub-Agents for Multiple Animations

If you need 3 or more overlays, render them in parallel sub-agents (one per slot):
```
Agent 1: bridge.add_lower_third(..., slot_id="lt1")
Agent 2: bridge.add_chapter_intro(..., slot_id="ch1")
Agent 3: bridge.add_title_card(..., slot_id="tc1")
```
Total wall time ≈ slowest one (not sum of all).

## Requirements
- Node.js >= 22 on PATH
- `npm install` run in workspace root (installs hyperframes CLI)
- `ffmpeg` on PATH
