---
name: workspace
description: >
  Master skill for the editing-workspace. Read this to understand the full
  capability set and which sub-skill to load for each task.
---

# Editing Workspace — Master Skill

This workspace gives you everything needed to go from raw footage to a
fully published-ready video: editing, motion graphics, captions,
timestamps, and thumbnails.

## Capability Map

| What you want to do | Load this skill |
|---|---|
| Cut / grade / render a video | `skills/video-editing.md` |
| Add animated overlays (lower thirds, title cards) | `skills/motion-graphics.md` |
| Write captions, descriptions, titles in user's style | `skills/captions.md` |
| Build YouTube chapter timestamps | `skills/timestamps.md` |
| Generate a thumbnail | `skills/thumbnails.md` |

## Output Convention

All outputs for every session go into:
```
<footage_dir>/edit/
```

**Never write into `tools/` or anywhere inside the workspace repo itself.**

## Tool Locations

| Tool | Path |
|---|---|
| video-use helpers | `tools/video-use/helpers/` |
| video-use SKILL.md | `tools/video-use/SKILL.md` |
| HyperFrames repo | `tools/hyperframes/` |
| Caption module | `modules/captions/` |
| Timestamp module | `modules/timestamps/` |
| Thumbnail module | `modules/thumbnails/` |
| Motion graphics bridge | `modules/motion_graphics/` |
| HTML templates | `templates/` |

## End-to-End Pipeline Order

1. **Drop footage** → any folder, user's choice
2. **Read `tools/video-use/SKILL.md`** → follow its process (transcribe → pack → converse → plan → execute → render)
3. **Motion graphics** → after EDL is locked, render animation slots with `modules/motion_graphics/bridge.py`, add to EDL `overlays` key
4. **Timestamps** → `python -m modules.timestamps generate --edit-dir <path>` (requires edl.json)
5. **Captions** → `python -m modules.captions generate --edit-dir <path> --platform youtube`
6. **Thumbnail** → `python -m modules.thumbnails generate --video <path> --edit-dir <path>`
