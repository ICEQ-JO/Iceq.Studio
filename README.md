# 🎬 Iceq Studio 

> **Your Open-Source AI Video Editing "Second Brain"**  
> We're revolutionizing how video editing scales. Drop raw footage into your folder. Open Obsidian or your code editor. Describe your edit in plain text. Get a fully cut, color-graded, motion-graphics-enhanced video back — plus captions, chapter timestamps, and thumbnails — **all without ever touching a video timeline.**

Iceq Studio is a completely open-source architecture that bridges LLM coding agents, Python scripting, headless browser rendering, and your Obsidian knowledge-base into a seamless video production pipeline.

---

## What makes Iceq Studio different?

Unlike standard video editors, the interface here is **text**. You (or your AI agent) read the transcript in Obsidian, highlight or cross out sentences, and the engine handles the math to cut the video perfectly with sub-second audio crossfades.

| Capability | Powered By |
|---|---|
| Headless cutting & grade | `browser-use/video-use` (transcript → FFmpeg) |
| Cinematic Motion Graphics | `heygen-com/hyperframes` (HTML/CSS → video) |
| Obsidian Native Integration | Dataview & Custom YAML Dashboards |
| AI Image Generations | Native Imagen 3 & DALL-E Compositing |
| AI-Aware Style Captions | `modules/captions/` |
| Deep YouTube Timestamps | `modules/timestamps/` |

---

## ⚡ Quick Start

### 1. Clone & Setup
```bash
git clone https://github.com/ICEQ-JO/Iceq.Studio.git
cd Iceq.Studio
./scripts/setup.sh
```

*(Note: `setup.sh` checks for Node ≥ 22, Python ≥ 3.11, and ffmpeg; runs npm installs, and registers AI agent skills).*

### 2. Connect Your Second Brain (Obsidian)
Turn your note-taking app into your editing suite:
```bash
cp .env.example .env
# Fill in ELEVENLABS_API_KEY (required for auto-cutting)
# Add your OPENAI_API_KEY for AI backgrounds / copy generation

./scripts/link-obsidian.sh "/path/to/your/Obsidian Vault"
```

### 3. Drop Footage
```bash
./scripts/new-project.sh /path/to/your/raw/footage
```
*(This automatically symlinks the heavy video files securely into your Obsidian Vault's `Video Projects` bucket without destroying your vault index.)*

### 4. Talk to your Agent
Spin up GitHub Copilot, Cursor, or Claude Code right in the `Iceq.Studio` folder and simply say:
> "Read AGENTS.md, then edit the footage in my recent project. Delete all the silence gaps and add a glassy iOS lower-third at the 10-second mark."

---

## 🧠 The "Second Brain" Workflow

Iceq Studio treats your video like a living document:
1. **Transcribe**: ElevenLabs creates a word-level diarized transcript.
2. **Review**: You open Obsidian and see every sentence your speaker said.
3. **Edit via Text**: Highlight the sentences you want to keep (`==like this==`). Strike out the ones you don't.
4. **Compile**: The backend pulls your instructions, writes the edit decision list, cuts the 4K footage perfectly, applies a color grade, layers HTML-rendered motion graphics, and burns subtitles.
5. **Publish**: Your Obsidian `Video Production Dashboard` is updated instantly with YouTube Timestamps, Instagram Captions matching your writing style, and the final MP4.

---

## Directory Map

```
Iceq.Studio/
├── AGENTS.md               ← CRITICAL: The brain file for any AI Agent you use.
├── WORKSPACE.md            ← Deep-dive technical reference on the engine.
├── skills/                 ← Agent instruction files (auto-discovered)
├── tools/                  
│   ├── video-use/          ← The headless cutting engine
│   └── hyperframes/        ← The headless animation engine
├── modules/
│   ├── images/             ← AI Generation bridging (DALL-E & Gemini)
│   ├── captions/           ← Style-aware social copy generators
│   └── timestamps/         ← YouTube Structural builders
├── dashboards/             ← Obsidian Dataview Kanban Templates
├── templates/              ← Hackable HTML Motion Graphic layers
└── scripts/                ← The glue
```

---

## Requirements

| Tool | Version | Purpose |
|---|---|---|
| Python | ≥ 3.11 | Control flow & ML bridging |
| Node.js | ≥ 22 | HyperFrames HTML Studio |
| ffmpeg | ≥ 4.x | Video processing & encode |
| ElevenLabs | API Key | Sub-second word gap targeting |

---

## Contributing

Iceq Studio is an ambitious open-source experiment to blur the lines between **Knowledge Management** and **Video Production**. 

Want to build? Feel free to:
- Add gorgeous CSS/HTML templates into `templates/` for motion graphics.
- Expand our `modules/images/` to support Midjourney.
- Submit Obsidian dashboard variants!

*See `WORKSPACE.md` for architecture details.*
---
*Built openly for creators, engineering teams, and AI Agent believers.*
