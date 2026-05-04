---
name: motion-graphics
description: >
  How to create and add animated motion graphics overlays.
  Editframe is the default backend (works with all LLMs).
  HyperFrames is the fallback for complex GSAP animations.
  Read this when adding overlays to a video.
---

# Motion Graphics Skill

Motion graphics in this workspace are rendered to MP4 and composited into
the video via the EDL `overlays` key.

**Default backend: Editframe** — uses `<ef-*>` HTML web components.
Works reliably with all major LLMs (GPT-4o, Gemini, Claude, Llama, etc.)
because it's a constrained declarative DSL, not free-form GSAP code.

**Fallback: HyperFrames** — use when you need complex, bespoke GSAP
animations beyond what standard CSS transitions can express.

Set backend in `.env`:
```
MOTION_GRAPHICS_BACKEND=editframe   # default
MOTION_GRAPHICS_BACKEND=hyperframes  # GSAP-heavy custom animations
```

---

## Workflow

1. **Choose a template** from `templates/editframe/` (or `templates/` for HyperFrames)
2. **Render it** using the Python bridge — one liner per animation slot
3. **Add to EDL** under `overlays` with `start_in_output` and `duration`
4. **Re-render** with `render.py` — clips are composited with correct PTS shift

---

## Editframe Template Catalog (default backend)

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

| Parameter | Type | Default |
|---|---|---|
| `name` | string | "Name" |
| `title` | string | "" |
| `accent_color` | hex | #FF5A00 |
| `bg_color` | string | rgba(10,10,10,0.88) |
| `duration` | float | 4.0 s |

---

### `title-card.html`
Full-screen title card with staggered word reveal + accent line draw.
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
Chapter transition (letter-spacing reveal, centered). 3 s recommended.
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
Corner subscribe animation (bottom-right pill + bell). 3 s.
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
Full-screen end screen with pulsing subscribe button. 15 s recommended.
```python
path = bridge.add_end_screen(
    channel_name="My Channel",
    tagline="New videos every week",
    output_dir=edit_dir,
    slot_id="end1",
    duration=15.0,
)
```

---

## Generic Render Call (Editframe)

Any `templates/editframe/*.html` file can be rendered with the generic call:
```python
from modules.motion_graphics import bridge

path = bridge.render_template(
    template_path="templates/editframe/lower-third.html",
    vars={
        "title":       "Main Text",
        "subtitle":    "Secondary Text",
        "accentColor": "#FF5A00",
        "bgColor":     "#0A0A0A",
        "font":        "Inter",
    },
    output_mp4="/path/to/edit/animations/slot_1/render.mp4",
    duration=4.0,
    fps=30,
    width=1920,
    height=1080,
)
```

> **Key difference from HyperFrames vars:**
> Editframe uses camelCase keys (`accentColor`, `bgColor`) instead of
> kebab-case (`accent-color`, `bg-color`). This matches `window.__EF_DATA__`
> JS conventions.

---

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
Overlays are applied BEFORE subtitles.

---

## Writing Custom Editframe Compositions (LLM-friendly guide)

Every Editframe composition follows this structure:
```html
<ef-configuration media-engine="local">
  <ef-timegroup mode="fixed" style="width:1920px; height:1080px;">

    <!-- Add elements here -->
    <ef-text style="position:absolute; bottom:80px; left:80px;
                    color:white; font-size:48px;
                    animation: fade-up 0.4s ease both;">
      My Text
    </ef-text>

  </ef-timegroup>
</ef-configuration>

<script>
  // Inject runtime data from bridge --data JSON
  const d = window.__EF_DATA__ || {};
  document.querySelector('ef-text').textContent = d.title || 'Default';
</script>
```

**Available elements:**
| Element | Purpose |
|---|---|
| `<ef-timegroup>` | Container (mode: fixed / sequence / contain) |
| `<ef-text>` | Text with optional `split="word"` stagger |
| `<ef-video>` | Video clip with `sourcein` / `sourceout` trim |
| `<ef-image>` | Static image |
| `<ef-audio>` | Audio track |
| `<ef-captions>` | Subtitle overlay |
| `<ef-waveform>` | Audio waveform visualizer |

---

## HyperFrames (Advanced / Custom GSAP Animations)

Use HyperFrames when you need animations that go beyond standard CSS:
- Complex GSAP timelines with ScrollTrigger-style sequencing
- Particle systems, shader effects
- Multi-layered choreography that Editframe CSS can't express

Switch to HyperFrames for a single render:
```python
from modules.motion_graphics import hf_render_template

path = hf_render_template(
    template_path="templates/ios-glassy-dynamic.html",
    vars={"title": "...", "accent-color": "#FF5A00"},
    output_mp4="edit/animations/slot_custom/render.mp4",
    duration=5.0,
)
```

Or set `MOTION_GRAPHICS_BACKEND=hyperframes` in `.env` to switch all calls.

---

## Parallel Sub-Agents for Multiple Animations

If you need 3+ overlays, render them in parallel sub-agents (one per slot):
```
Agent 1: bridge.add_lower_third(..., slot_id="lt1")
Agent 2: bridge.add_chapter_intro(..., slot_id="ch1")
Agent 3: bridge.add_title_card(..., slot_id="tc1")
```
Total wall time ≈ slowest one (not sum of all).

---

## Requirements
- Node.js >= 18 on PATH
- `npm install` run in workspace root (installs both hyperframes and @editframe/cli)
- `ffmpeg` on PATH
