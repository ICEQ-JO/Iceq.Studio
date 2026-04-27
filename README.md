# 🎬 Editing Workspace

> **An open-source AI video editing workspace.**  
> Drop raw footage in a folder. Describe what you want. Get a fully edited, color-graded, motion-graphics-enhanced video back — plus captions, timestamps, and thumbnails — all without touching a timeline.

---

## What this workspace does

| Capability | Tool |
|---|---|
| Cut, grade, and export video | `tools/video-use` (browser-use/video-use) |
| High-grade HTML motion graphics | `tools/hyperframes` (heygen-com/hyperframes) |
| Style-matched captions & descriptions | `modules/captions/` |
| YouTube chapter timestamp structure | `modules/timestamps/` |
| Thumbnail generation (frame + composite) | `modules/thumbnails/` |

---

## Quick Start (Human)

### 1. Clone & Setup
```bash
git clone https://github.com/your-username/editing-workspace.git
cd editing-workspace
./scripts/setup.sh
```

`setup.sh` checks for Node ≥ 22, Python ≥ 3.11, and ffmpeg; installs all deps; and registers agent skills.

### 2. Add your API key
```bash
cp .env.example .env
# Fill in ELEVENLABS_API_KEY (required)
# Optionally add OPENAI_API_KEY for AI-powered captions
```

### 3. Start a project
```bash
./scripts/new-project.sh /path/to/your/footage
```

### 4. Open an agent and say:
```
Read AGENTS.md, then edit the footage in /path/to/your/footage into a final video.
```

---

## Quick Start (Coding Agent)

```
Read /path/to/editing-workspace/AGENTS.md first. Then follow the instructions there.
```

That's it. The workspace self-documents for agents.

---

## Directory Map

```
editing-workspace/
├── AGENTS.md               ← Start here if you're an AI agent
├── WORKSPACE.md            ← Detailed workspace reference
├── skills/                 ← Agent skill files (auto-discovered)
│   ├── workspace.md
│   ├── video-editing.md
│   ├── motion-graphics.md
│   ├── captions.md
│   ├── timestamps.md
│   └── thumbnails.md
├── tools/
│   ├── video-use/          ← browser-use/video-use (transcript → FFmpeg)
│   └── hyperframes/        ← heygen-com/hyperframes (HTML → video)
├── modules/
│   ├── captions/           ← Style-aware caption & description generator
│   ├── timestamps/         ← Full chapter timestamp builder
│   ├── thumbnails/         ← Frame extractor + compositor
│   └── motion_graphics/    ← Python ↔ HyperFrames bridge
├── templates/              ← Reusable HyperFrames HTML motion graphic templates
│   ├── lower-third.html
│   ├── title-card.html
│   ├── chapter-intro.html
│   ├── end-screen.html
│   └── subscribe-bump.html
├── examples/               ← End-to-end worked examples
│   ├── tutorial-video/
│   └── talking-head/
└── scripts/
    ├── setup.sh
    ├── new-project.sh
    └── generate-all.sh
```

---

## Full Workflow (end-to-end)

```
Raw Footage
    │
    ▼  tools/video-use
  Transcribe (ElevenLabs Scribe — word-level)
    │
    ▼
  Agent reads transcript, converses with you, proposes edit strategy
    │
    ▼  tools/video-use + tools/hyperframes
  Edit → Color Grade → Motion Graphics Overlays → Render final.mp4
    │
    ▼  modules/timestamps
  Generate YouTube chapter timestamps
    │
    ▼  modules/captions
  Generate title options, description, and captions in your writing style
    │
    ▼  modules/thumbnails
  Extract best frame → Composite thumbnail (PIL or HyperFrames)
    │
    ▼
  final.mp4 + timestamps.txt + description.md + thumbnail.png
  → all in <footage_dir>/edit/
```

---

## Requirements

| Tool | Version | Purpose |
|---|---|---|
| Python | ≥ 3.11 | All modules + video-use helpers |
| Node.js | ≥ 22 | HyperFrames CLI |
| ffmpeg | ≥ 4.x | Video rendering |
| ElevenLabs key | — | Transcription (required) |
| OpenAI or Anthropic key | — | Caption generation (optional) |

---

## Contributing

This is an open-source project. Feel free to:
- Add new HyperFrames templates to `templates/`
- Add new caption styles or platform targets to `modules/captions/`
- Improve the timestamp generator heuristics in `modules/timestamps/`
- Add example projects to `examples/`

See `WORKSPACE.md` for architecture details.

---

## Upstream Projects

- **video-use**: [github.com/browser-use/video-use](https://github.com/browser-use/video-use) — Apache 2.0
- **HyperFrames**: [github.com/heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) — Apache 2.0

---

## License

MIT
