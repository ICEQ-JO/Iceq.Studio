# Walkthrough: Talking Head Interview

This example shows an end-to-end session for a **single-camera talking head** —
the most common YouTube format. One speaker, multiple takes, lower-third title card,
subscribe bump, warm cinematic grade, and 2-word UPPERCASE subtitles.

---

## Source Material

```
/footage/interview/
├── CLIP_A.mp4    (95s — 2 takes in one file, natural break at 44s)
├── CLIP_B.mp4    (105s — middle content, HVAC noise appears at 90s)
├── CLIP_C.mp4    (40s — outro/CTA, 2 takes)
```

---

## Step 1 — Setup

```bash
./scripts/new-project.sh /footage/interview
```

---

## Step 2 — Transcribe All Takes

```bash
python tools/video-use/helpers/transcribe_batch.py /footage/interview/
python tools/video-use/helpers/pack_transcripts.py --edit-dir /footage/interview/edit/
```

---

## Step 3 — Agent Conversation

```
Read AGENTS.md and skills/video-editing.md.

This is a talking-head interview. The speaker is discussing a personal turning point
in their career. Footage is in /footage/interview/.

Goals:
- Cut to ~2m30s total
- Remove all filler words and dead air
- Warm cinematic grade (speaker on neutral background)
- 2-word UPPERCASE subtitle style
- Add lower-third with speaker name and title

Please read takes_packed.md, pre-scan for verbal slips, 
propose a story structure, and wait for my OK before editing.
```

### Strategy the Agent Will Propose

> "I found a strong hook in CLIP_A at 2.8s — 'Tuesday afternoon' creates intrigue.
> CLIP_B has the core problem framing but HVAC ruins after 90s — cutting at 87.3s.
> CLIP_C has the cleanest CTA across both takes.
>
> Structure: HOOK (16s) → PROBLEM (63s) → SOLUTION (28s) → CTA (29s) = 2m16s.
>
> Grade: warm_cinematic — suits the personal storytelling tone.
> Subtitle style: 2-word UPPERCASE chunks, bottom-center.
>
> Motion graphics: lower-third for speaker name at 6s, subscribe bump in final 30s.
>
> Shall I proceed?"

---

## Step 4 — Motion Graphics

```python
from modules.motion_graphics import bridge

edit_dir = "/footage/interview/edit"

# Lower-third (appears at output second 6.0)
bridge.add_lower_third(
    name="Khalid Al-Mansouri",
    title="Product Designer",
    output_dir=edit_dir,
    slot_id="lt1",
    duration=4.0,
    accent_color="#FF5A00",
)

# Subscribe bump (appears at output second 105.5, last 38s of video)
bridge.add_subscribe_bump(
    output_dir=edit_dir,
    slot_id="sub1",
    duration=3.0,
)
```

---

## Step 5 — Render

```bash
# Fast preview
python tools/video-use/helpers/render.py edit/edl.json -o edit/preview.mp4 --preview

# Final with subtitles
python tools/video-use/helpers/render.py edit/edl.json -o edit/final.mp4 --build-subtitles
```

---

## Step 6 — Post-Production Assets

```bash
./scripts/generate-all.sh /footage/interview/edit/ --platform youtube
```

For Instagram as well:
```bash
python -m modules.captions generate --edit-dir /footage/interview/edit/ --platform instagram
```

---

## Self-Evaluation Checklist

Before showing the user anything, the agent verifies:
- [ ] No audio pops at cut boundaries (30ms fade rule)
- [ ] Lower-third appears BELOW any subtitle lines
- [ ] Subscribe bump visible, not hidden by subtitles
- [ ] Grade consistent across all segments (check first/last/midpoints)
- [ ] Total duration matches EDL expectation (~144s)

---

## Final Output

```
/footage/interview/edit/
├── final.mp4               (2m24s, warm grade, lower-third, subscribe bump, subtitles)
├── timestamps.txt          ("0:00 Introduction\n0:16 The Problem\n1:19 The Solution\n1:47 Outro")
├── title_options.md        (5 title options)
├── description.md          (YouTube description with timestamps)
├── caption_youtube.md      (community post)
├── caption_instagram.md    (Instagram caption with hashtags)
└── thumbnail.png           (sharpest frame from HOOK with title overlay)
```
