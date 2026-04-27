---
name: editing-workspace
description: >
  An open-source AI video editing workspace. Edit videos with high-grade motion graphics,
  generate style-matched captions and descriptions, build full timestamp structures,
  and create thumbnails — all via conversation with a coding agent.
---

# Editing Workspace — Agent Instructions

**Read this file at the start of every session.**

---

## What this workspace is

A fully self-contained editing environment for AI agents. You have access to:

1. **`tools/video-use/`** — Full transcript-driven video editing pipeline (cut, grade, subtitle, render)
2. **`tools/hyperframes/`** — HTML-to-video motion graphics renderer (overlays, title cards, lower thirds)
3. **`modules/`** — Custom Python modules for captions, timestamps, and thumbnails
4. **`templates/`** — Pre-built HyperFrames HTML motion graphic templates
5. **`skills/`** — Detailed skill files for each capability (read the relevant one for your task)

---

## Hard Rules (non-negotiable)

1. **Never write outputs into `tools/`** — those directories are upstream vendor code, keep them clean.
2. **All session outputs go into `<footage_dir>/edit/`** — timestamps, captions, thumbnails, final.mp4, everything.
3. **Never re-transcribe cached sources** — check `edit/transcripts/` first. Transcription costs real money.
4. **Always confirm strategy before executing** — describe your plan in plain English, wait for user confirmation, then execute.
5. **Read the appropriate skill file before starting any task** — don't guess at APIs, the skills document the actual function signatures.
6. **Never commit .env or API keys** — they are in .gitignore, keep them there.
7. **Obsidian Frontmatter** — If the user is using the Obsidian Vault sync, all generated `.md` files will have YAML frontmatter. If you edit a file, preserve the frontmatter.

---

## Skill Files — Load These For Each Task

| Task | Skill file to read |
|------|-------------------|
| Edit / cut / grade a video | `skills/video-editing.md` |
| Add motion graphics overlays | `skills/motion-graphics.md` |
| Generate captions, titles, descriptions | `skills/captions.md` |
| Build YouTube timestamp chapters | `skills/timestamps.md` |
| Generate thumbnails | `skills/thumbnails.md` |
| Generate AI images/backgrounds | `skills/image-generation.md` |
| Understand the full workspace | `skills/workspace.md` |

---

## Standard Output Layout

After any editing session, the output directory looks like this:

```
<footage_dir>/
├── <raw source files — never touch these>
└── edit/
    ├── project.md              ← session memory, appended each run (has YAML frontmatter)
    ├── takes_packed.md         ← phrase-level transcript (primary reading view, has YAML)
    ├── edl.json                ← cut decisions
    ├── transcripts/<name>.json ← cached ElevenLabs JSON (immutable)
    ├── animations/slot_<id>/   ← per-animation renders
    ├── clips_graded/           ← per-segment extracts with grade applied
    ├── master.srt              ← output-timeline subtitles
    ├── timestamps.md           ← YouTube chapter timestamps (if generated, has YAML)
    ├── description.md          ← video description (if generated, has YAML)
    ├── caption_*.md            ← platform captions (has YAML)
    ├── title_options.md        ← 5 title candidates (if generated, has YAML)
    ├── thumbnail.png           ← final thumbnail (if generated)
    ├── style_profile.json      ← user writing style cache (persists across projects)
    ├── verify/                 ← debug frames / timeline PNGs
    ├── preview.mp4
    └── final.mp4
```

---

## Cold-Start Checklist

On the first message of each session, or when starting a new video project:

1. Check if `edit/project.md` exists — if yes, read it and summarize the last session in one sentence. It may be part of an Obsidian Vault.
2. If `takes_packed.md` is present, read it carefully. Look for Obsidian highlights like `==this text==` or `**bold text**` — the user has placed these to indicate sections they definitely want kept in the cut.
3. Confirm that `ffmpeg` and `ffprobe` are on PATH: `ffmpeg -version`
4. Confirm the ElevenLabs key resolves (from `.env` or environment).
5. **CRITICAL:** Before taking any editing action, you MUST explicitly ask the user for their editing preferences. Ask them:
   - "Do you want me to automatically delete silence moments or filler words?"
   - "What motion graphics (lower thirds, title cards, subscribe bumps) should I add, and what colors/text should they have?"
6. Only proceed to generate the EDL or render once the user has answered.

---

## Capabilities Summary

### Video Editing (tools/video-use)
- Transcription via ElevenLabs Scribe (word-level, speaker diarization)
- Cut selection from transcript: filler removal, retake selection, silence gaps
- Color grading via ffmpeg filter chains (warm_cinematic, neutral_punch, or custom)
- 30ms audio fades at every cut (hardcoded rule — never skip)
- Animated subtitle burning (subtitles applied LAST, after all overlays)
- Self-evaluation loop before showing user anything

### Motion Graphics (tools/hyperframes)
- Write compositions as HTML with data attributes
- Render to MP4 with `npx hyperframes render`
- Pre-built templates in `templates/` — lower-third, title card, chapter intro, end screen
- Python bridge at `modules/motion_graphics/bridge.py` for programmatic rendering
- Integrates with video-use EDL via the `overlays` key

### Captions & Descriptions (modules/captions)
- Learns and stores user writing style in `style_profile.json`
- Generates: YouTube titles, video description, Instagram caption, LinkedIn post
- Style analysis from sample texts provided by the user
- CLI: `python -m modules.captions generate --edit-dir <path> [--platform youtube|instagram|linkedin]`

### Timestamps (modules/timestamps)
- Reads `takes_packed.md` + `edl.json` to generate chapter structure
- Outputs clean YouTube format: `0:00 Introduction`, `1:23 Problem`, etc.
- CLI: `python -m modules.timestamps generate --edit-dir <path>`

### Thumbnails (modules/thumbnails)
- Extracts candidate frames from video at key timestamps
- Fast path: PIL compositor (`compose_thumbnail_pil`)
- High-quality path: HyperFrames HTML template renderer (`compose_thumbnail_hyperframes`)
- CLI: `python -m modules.thumbnails generate --video <path> --edit-dir <path>`

---

## Setup (if not already done)

```bash
cd /path/to/editing-workspace
./scripts/setup.sh
```

This installs all Python and Node deps, checks system requirements, and registers skills with Claude Code / Codex if those agents are detected.
