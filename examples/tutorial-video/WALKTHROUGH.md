# Walkthrough: Tutorial Video

This example shows an end-to-end editing session for a **screen-share tutorial video**
with multiple takes, chapter intros, subtitles, and a generated thumbnail.

---

## Source Material

```
/footage/tutorial/
├── INTRO_TAKE1.mp4    (25s — intro, one false start)
├── INTRO_TAKE2.mp4    (22s — cleaner but flat delivery)
├── SETUP_TAKE1.mp4    (45s — good but stumbles on "dependencies")
├── SETUP_TAKE2.mp4    (40s — best take overall)
├── DEMO_TAKE1.mp4    (93s — single clean take)
├── RECAP_TAKE1.mp4   (30s — natural, direct to camera)
```

---

## Step 1 — Setup

```bash
# From workspace root
./scripts/new-project.sh /footage/tutorial
```

This creates `/footage/tutorial/edit/` with the directory skeleton.

---

## Step 2 — Transcribe

```bash
python tools/video-use/helpers/transcribe_batch.py /footage/tutorial/
python tools/video-use/helpers/pack_transcripts.py --edit-dir /footage/tutorial/edit/
```

This produces `edit/transcripts/*.json` and `edit/takes_packed.md`.

---

## Step 3 — Agent Conversation

Tell your agent:

```
Read /path/to/editing-workspace/AGENTS.md and skills/video-editing.md.

I have a tutorial video on how to do X in 10 minutes. The footage is in 
/footage/tutorial/. The transcripts are packed at edit/takes_packed.md.

Please:
1. Read the packed transcript and pre-scan for verbal slips.
2. Propose an edit strategy with chapter structure.
3. Wait for my confirmation before executing.
```

The agent will read `takes_packed.md`, describe what it sees, and propose
a strategy. You'll see something like:

> "I found 6 takes across 4 sections. Take 2 is cleanest for SETUP.
> I'll cut the INTRO false start at 13.2s. Structure: HOOK (11s) → SETUP (35s) 
> → DEMO (90s) → RECAP (26s). Total ~2m10s.
> I'll add chapter intros at each section boundary.
> Color grade: neutral_punch (screen content looks better without warm tones).
> Shall I proceed?"

---

## Step 4 — Motion Graphics

After you confirm and the EDL is locked:

```python
from modules.motion_graphics import bridge

edit_dir = "/footage/tutorial/edit"

# Title card for intro
bridge.add_title_card(
    title="How to Do X in 10 Minutes",
    output_dir=edit_dir,
    slot_id="tc1",
    duration=5.0,
)

# Chapter intros (render in parallel sub-agents in a real session)
bridge.add_chapter_intro("Setup", edit_dir, slot_id="ch1", chapter_number="01")
bridge.add_chapter_intro("Live Demo", edit_dir, slot_id="ch2", chapter_number="02")
```

Add the resulting paths to the EDL `overlays` key (see `edl.example.json`).

---

## Step 5 — Render

```bash
# Preview at 720p (fast check)
python tools/video-use/helpers/render.py edit/edl.json -o edit/preview.mp4 --preview

# Final at 1080p with subtitles burned in
python tools/video-use/helpers/render.py edit/edl.json -o edit/final.mp4 --build-subtitles
```

---

## Step 6 — Post-Production Assets

```bash
# Generate timestamps, captions, and thumbnail in one command
./scripts/generate-all.sh /footage/tutorial/edit/ --platform youtube
```

---

## Final Output

```
/footage/tutorial/edit/
├── final.mp4           (2m11s, color graded, subtitles, chapter intros)
├── timestamps.txt      ("0:00 Introduction\n0:11 Setup\n0:46 Live Demo\n2:09 Recap")
├── title_options.md    (5 YouTube titles)
├── description.md      (full description with timestamps embedded)
├── caption_youtube.md  (community post)
└── thumbnail.png       (frame from RECAP with title overlay)
```
