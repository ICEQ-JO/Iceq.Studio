# Iceq Studio

Hey, I’m **Khalid Khudari**. I built Iceq Studio because I was tired of spending more time clicking around editing software than actually making things.

This is an open-source AI video editing workspace for **solo founders, creators, and small teams** who want to ship high-grade video without hiring an editor or learning a dozen tools. You bring the footage and the idea; the agent handles the cuts, motion graphics, thumbnails, captions, timestamps, and final render.

I designed it to work with the coding agents I actually trust and use myself. In my experience, the strongest models for this kind of work are **GLM 5.2**, **Claude Opus 4.6**, and **Claude Opus 4.8**. The workspace runs great with **Claude Code**, **Kimi Code**, **OpenCode**, and **Pi Agents**. Basically any agent that can read the skill files and run Python/Node commands.

---

## What it actually does

Iceq Studio turns raw footage into a finished, publish-ready video through conversation with an AI agent:

1. **Transcribe** your footage with ElevenLabs Scribe (word-level, speaker-aware).
2. **Edit by text**: the agent reads the transcript, suggests cuts, and builds an `edl.json`.
3. **Add motion graphics**: lower thirds, title cards, chapter intros, subscribe bumps, end screens.
4. **Render** the final video with color grade, overlays, and burned-in subtitles.
5. **Generate packaging**: thumbnails, YouTube titles/descriptions, chapter timestamps, and platform captions.

The agent does the tedious work. You stay in the driver’s seat approving the creative decisions.

---

## What’s inside

```
Iceq.Studio/
├── AGENTS.md               # Instructions for AI agents
├── WORKSPACE.md            # Technical architecture reference
├── skills/                 # Skill files the agent reads per task
├── tools/
│   ├── video-use/          # Core video editing engine (transcript-driven)
│   └── hyperframes/        # Motion graphics engine (HTML/CSS to video)
├── modules/
│   ├── images/             # AI image generation (OpenAI / Gemini)
│   ├── captions/           # Captions, titles, descriptions
│   ├── timestamps/         # YouTube chapter timestamps
│   ├── thumbnails/         # Thumbnail generator + A/B variants
│   ├── motion_graphics/    # Bridge for HyperFrames / Editframe
│   ├── transcription/      # Hash-cached transcription wrapper
│   ├── verify/             # Render quality checks
│   └── observability.py    # Structured logging
├── templates/              # HTML motion graphic templates
├── dashboards/             # Obsidian dashboard templates
└── scripts/                # Setup and utility scripts
```

### The agent instructions

- **`AGENTS.md`** is the first file any coding agent should read. It tells the agent how the workspace is organized, what commands it can run, and what rules to follow so it doesn’t wander off.
- **`WORKSPACE.md`** is a deeper technical map of the architecture, file formats, and how the modules talk to each other. Useful when you want the agent to extend the system rather than just edit a video.
- **`skills/`** contains small Markdown skill files that teach the agent how to do one thing well: build an EDL, design a thumbnail, render a motion graphic, etc. The agent reads only the skills it needs for the current task.

### The engines

- **`tools/video-use/`** is the core video editor. It takes an `edl.json` (a text-based edit decision list) and renders the final cut. This is transcript-driven editing: you tell the agent “cut the ums, keep the story about the launch,” and it turns that into precise cuts.
- **`tools/hyperframes/`** is the motion graphics engine. It renders HTML/CSS templates to video, so you can design title cards, lower thirds, and end screens with normal web tech instead of After Effects.

### The modules

- **`modules/transcription/`** wraps ElevenLabs Scribe with file hashing and caching. If you re-render the same footage, it doesn’t re-transcribe, which saves time and API credits.
- **`modules/images/`** generates AI images for thumbnails and graphics using OpenAI and Gemini models.
- **`modules/captions/`** writes titles, descriptions, and platform-specific captions from the transcript or your notes.
- **`modules/timestamps/`** builds YouTube chapter timestamps automatically from the edited structure.
- **`modules/thumbnails/`** generates thumbnails plus A/B variants so you can pick the one that converts best.
- **`modules/motion_graphics/`** bridges the editing engine with HyperFrames so motion graphics are synced to the right frames.
- **`modules/verify/`** is the quality gate for renders. It checks that the output file exists, has the right duration, and didn’t silently fail.
- **`modules/observability.py`** provides structured logging so when something breaks, you can actually trace what happened.

### The templates and dashboards

- **`templates/`** holds HTML/CSS motion graphic templates. Duplicate one, tweak the style, and you’ve got a new look without rebuilding the engine.
- **`dashboards/`** has Obsidian dashboard templates for tracking projects, notes, and renders. This is what turns an Obsidian vault into a video production hub.
- **`scripts/`** contains setup and helper scripts. Run `./scripts/setup.sh` once, then `./scripts/new-project.sh` for each new video.

---

## Setup

Iceq Studio works with **Claude Code**, **Kimi Code**, **OpenCode**, **Pi Agents**, or any LLM coding agent that can read Markdown skills and run shell commands.

1. **Clone the repo:**
   ```bash
   git clone https://github.com/ICEQ-JO/Iceq.Studio.git
   cd Iceq.Studio
   ```

2. **Run setup:**
   ```bash
   ./scripts/setup.sh
   ```
   This installs Python/Node deps and pulls the vendored `video-use` and `hyperframes` engines into `tools/`.

3. **Add your API keys** to a `.env` file in the root:
   ```bash
   ELEVENLABS_API_KEY=your_key_here    # Required for transcription
   OPENAI_API_KEY=your_key_here        # Optional: captions / AI images
   ANTHROPIC_API_KEY=your_key_here     # Optional: captions
   GEMINI_API_KEY=your_key_here        # Optional: Imagen 3 images
   ```

---

## How to use it

1. **Start a project:**
   ```bash
   ./scripts/new-project.sh /path/to/your/footage_folder
   ```

2. **Open the folder in your agent** and say something like:
   > “Read AGENTS.md and start editing the video in /path/to/footage.”

3. **Guide the edit.** The agent will ask about your preferences, like keep/drop silences, motion graphics style, colors, etc. Answer in plain English.

4. **Render.** The agent builds `edl.json` and runs the render pipeline to produce `edit/final.mp4`.

5. **Optional:** use the Obsidian dashboard to track progress, or highlight sections in `edit/takes_packed.md` to tell the agent what to keep.

---

## Why I built this

I believe solo founders and creators should be able to produce studio-quality video without a studio. Most AI video tools today are either locked behind subscriptions or force you into a rigid workflow. I wanted something **open, modular, and agent-first**, so the workflow adapts to you, not the other way around.

This is for the community of people building in public, shipping alone, and figuring it out as they go. If this helps you publish one more video, or frees up an afternoon, it was worth building.

---

## License

MIT. Use it, fork it, break it, improve it.
