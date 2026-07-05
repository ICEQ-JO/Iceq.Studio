# Editing Workspace — Architecture Reference

This document explains the architecture, module contracts, and design decisions for contributors and advanced users.

---

## Design Philosophy

1. **Text is the interface.** Agents read transcripts, not videos. Visuals are consulted on-demand at decision points.
2. **Audio is primary, visuals follow.** All cut decisions start from speech boundaries and silence gaps.
3. **Ask → confirm → execute → persist.** Never touch the cut until the user approves the strategy.
4. **Outputs are isolated.** All session artifacts live in `<footage_dir>/edit/`. The workspace repo stays clean.
5. **Modular by capability.** Each module (captions, timestamps, thumbnails, motion graphics) is independently usable. They are also composable: the timestamp module reads the same `edl.json` that the video-use pipeline produces.
6. **Agent-first, human-usable.** Everything has a CLI, which means humans can call it too.

---

## Module Contracts

### `modules/captions`

**Input:** Transcript text, user writing style samples (optional), platform target  
**Output:** Title options, description, caption (platform-specific), all saved to `edit/`

**StyleProfile** is cached in `edit/style_profile.json`. On first run, the agent either:
- Asks the user to paste 2–3 sample texts written in their own style
- Or uses heuristics from the existing transcript if no samples are available

The profile persists across projects if saved to a shared location. A project can override it.

### `modules/timestamps`

**Input:** `edit/takes_packed.md` + `edit/edl.json`  
**Output:** `edit/timestamps.txt` (YouTube format)

Logic: each `beat` label in the EDL becomes a chapter. The function maps output-timeline offset (seconds) → YouTube timestamp (`M:SS` or `H:MM:SS`).

### `modules/thumbnails`

**Input:** `final.mp4` or any source video, `edit/edl.json` for candidate timestamps  
**Output:** `edit/thumbnail.png`

Two rendering paths:
- **PIL path** — fast, fully local. Loads the best frame with Pillow, overlays text with a chosen font, and saves PNG.
- **HyperFrames path** — higher quality. Renders a HTML template (`templates/*.html`) to a 1280×720 PNG via the HyperFrames CLI. Requires Node ≥ 22.

### `modules/motion_graphics`

**Input:** Template HTML path + template variables (title, name, color etc.)  
**Output:** `<edit>/animations/slot_<id>/render.mp4`

The bridge wraps `npx hyperframes render` and injects variables via HTML data attributes. Rendered clips are referenced in the EDL under `overlays` and composited by `tools/video-use/helpers/render.py`.

---

## Template Variables (HyperFrames)

All `templates/*.html` files support a standard set of variables injected via the bridge:

| Variable | Type | Description |
|---|---|---|
| `data-title` | string | Main text line |
| `data-subtitle` | string | Secondary text line |
| `data-accent-color` | hex | Accent/highlight color |
| `data-bg-color` | hex | Background color |
| `data-duration` | float | Composition duration in seconds |
| `data-font` | string | Font family name |

The bridge passes these via `--var key=value` flags to the HyperFrames CLI.

---

## EDL Integration (video-use ↔ HyperFrames)

The video-use EDL format already has an `overlays` key. Motion graphics slots plug in here:

```json
{
  "overlays": [
    {
      "file": "edit/animations/slot_1/render.mp4",
      "start_in_output": 0.0,
      "duration": 5.0
    },
    {
      "file": "edit/animations/slot_2/render.mp4",
      "start_in_output": 45.2,
      "duration": 3.0
    }
  ]
}
```

`tools/video-use/helpers/render.py` handles the compositing with correct PTS shifting (Hard Rule 4 from SKILL.md).

---

## Environment Variables

| Variable | Required | Used by |
|---|---|---|
| `ELEVENLABS_API_KEY` | Yes | `tools/video-use` — transcription |
| `OPENAI_API_KEY` | No | `modules/captions` — style-matched generation |
| `ANTHROPIC_API_KEY` | No | `modules/captions` — alternative LLM |
| `CAPTION_LLM_BACKEND` | No | `modules/captions` — selects LLM |

---

## Upstream Vendoring Strategy

`tools/video-use` and `tools/hyperframes` are **vendored upstream copies**. They are pulled automatically by `scripts/setup.sh` (via `scripts/pull-tools.sh`) and are ignored by git so the workspace repo stays small and upstream history is preserved.

- After cloning, run `./scripts/setup.sh` to fetch the tools.
- To pull the latest upstream versions manually:
  ```bash
  ./scripts/pull-tools.sh
  ```
- If you prefer git subtrees and have `git-subtree` installed, you can still use:
  ```bash
  git subtree pull --prefix tools/video-use https://github.com/browser-use/video-use.git main --squash
  git subtree pull --prefix tools/hyperframes https://github.com/heygen-com/hyperframes.git main --squash
  ```
- Never modify files in `tools/` — changes will be overwritten on the next pull.

---

## Adding a New Template

1. Create `templates/<name>.html` following the HyperFrames composition format.
2. Add a variable table to `skills/motion-graphics.md` under the template catalog section.
3. Optionally add a Python convenience function to `modules/motion_graphics/bridge.py`.

## Adding a New Caption Platform

1. Add a new branch to `modules/captions/generator.py` under `generate_caption()`.
2. Add usage notes to `skills/captions.md`.

## Adding a New Example

1. Create `examples/<name>/WALKTHROUGH.md` with a step-by-step narrative.
2. Create `examples/<name>/edl.example.json` with a realistic (anonymized) EDL.
