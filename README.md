# Iceq Studio

Made by Khalid Khudari

An open-source AI video editing workspace. This project allows you to edit videos using AI agents by transcribing footage, cutting based on text, and adding motion graphics.

## File Structure

```
Iceq.Studio/
├── AGENTS.md               # Instructions for AI agents
├── WORKSPACE.md            # Technical architecture reference
├── skills/                 # Skill files providing context to agents
├── tools/                  
│   ├── video-use/          # Core video editing engine (transcript-driven)
│   └── hyperframes/        # Motion graphics engine (HTML/CSS to video)
├── modules/
│   ├── images/             # AI Image generation (OpenAI/Gemini)
│   ├── captions/           # Captions and description generators
│   ├── timestamps/         # YouTube timestamp generator
│   ├── thumbnails/         # Thumbnail generator
│   └── motion_graphics/    # Bridge for HyperFrames
├── templates/              # HTML templates for motion graphics
├── dashboards/             # Obsidian Dataview templates
└── scripts/                # Setup and utility scripts
```

## Setup & Connecting LLMs

Iceq Studio is designed to be used with any LLM coding agent (Cursor, Claude Code, GitHub Copilot, etc.).

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ICEQ-JO/Iceq.Studio.git
   cd Iceq.Studio
   ```

2. **Run setup:**
   ```bash
   ./scripts/setup.sh
   ```

3. **Configure Environment:**
   Create a `.env` file in the root directory:
   ```bash
   ELEVENLABS_API_KEY=your_key_here    # Required for transcription
   OPENAI_API_KEY=your_key_here         # Optional: for captions/images
   GEMINI_API_KEY=your_key_here         # Optional: for Imagen 3
   OBSIDIAN_VAULT_PATH=path_to_vault    # Optional: for Obsidian integration
   ```

## How to Use

1. **Initialize a Project:**
   ```bash
   ./scripts/new-project.sh /path/to/your/footage_folder
   ```

2. **Start Editing with an Agent:**
   Open this folder in your preferred AI-powered editor (e.g., Cursor) or start an agent (e.g., Claude Code). Give it the following instruction:
   > "Read AGENTS.md and start editing the video in [folder path]."

3. **Obsidian Workflow:**
   If linked, use the Obsidian "Video Production Dashboard" to monitor transcription and edit progress. Highlight text in `takes_packed.md` to tell the agent which parts to keep.

4. **Render:**
   The agent will generate an `edl.json` and run the render script to produce `final.mp4` in the project's `edit/` directory.
