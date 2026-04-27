---
name: video-editing
description: >
  How to edit, cut, color grade, and render videos using the video-use tool
  inside this workspace. Read this before starting any editing session.
---

# Video Editing Skill

## Primary Reference

**Always read `tools/video-use/SKILL.md` first.** It contains the complete
editing process, cut craft, EDL format, helper API, hard rules, and anti-patterns.

This file adds workspace-specific notes on top.

## Workspace-Specific Rules

1. **Python helpers** are at `tools/video-use/helpers/`. Run them as:
   ```bash
   python tools/video-use/helpers/transcribe.py <video>
   python tools/video-use/helpers/render.py edl.json -o edit/final.mp4
   ```

2. **Output directory**: always `<footage_dir>/edit/` — the `video-use/` tool directory stays clean.

3. **ElevenLabs key**: must be in `.env` at the workspace root, or in environment:
   ```bash
   source /path/to/editing-workspace/.env  # or set ELEVENLABS_API_KEY directly
   ```

4. **Motion graphics overlays**: after the EDL is locked, use `skills/motion-graphics.md`
   to render HyperFrames slots. Add the resulting clip paths to the EDL `overlays` key.

## Quick Command Reference

```bash
# Transcribe a single file
python tools/video-use/helpers/transcribe.py /path/to/video.mp4

# Batch transcribe a directory
python tools/video-use/helpers/transcribe_batch.py /path/to/footage/

# Pack transcripts into the primary reading view
python tools/video-use/helpers/pack_transcripts.py --edit-dir /path/to/edit/

# Visual drill-down at a specific time range
python tools/video-use/helpers/timeline_view.py /path/to/video.mp4 10.0 15.0

# Render from EDL (preview)
python tools/video-use/helpers/render.py edit/edl.json -o edit/preview.mp4 --preview

# Render final (full quality, burn subtitles inline)
python tools/video-use/helpers/render.py edit/edl.json -o edit/final.mp4 --build-subtitles
```

## EDL Format Reference

```json
{
  "version": 1,
  "sources": { "CLIP1": "/abs/path/CLIP1.MP4" },
  "ranges": [
    {
      "source": "CLIP1",
      "start": 2.42,
      "end": 6.85,
      "beat": "HOOK",
      "quote": "Ninety percent of what a web agent does is wasted.",
      "reason": "Cleanest delivery."
    }
  ],
  "grade": "warm_cinematic",
  "overlays": [
    { "file": "edit/animations/slot_lt1/render.mp4", "start_in_output": 0.0, "duration": 4.0 }
  ],
  "subtitles": "edit/master.srt",
  "total_duration_s": 87.4
}
```

**Beat labels** become chapter names in **timestamps** and section names in **descriptions**.
Use consistent, ALL-CAPS labels: HOOK, PROBLEM, SOLUTION, BENEFIT, EXAMPLE, CTA, etc.
