#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# scripts/setup.sh
# Full workspace setup script.
# Run once after cloning: ./scripts/setup.sh
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

WORKSPACE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$WORKSPACE_ROOT"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ok()   { echo -e "${GREEN}✅ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
fail() { echo -e "${RED}❌ $1${NC}"; }

echo ""
echo "🎬  Editing Workspace Setup"
echo "    $(pwd)"
echo ""

ERRORS=0

# ── 1. System Requirements ───────────────────────────────────────────────────

echo "── Checking system requirements ──────────────────────────────────────"

# Python
if command -v python3 >/dev/null 2>&1; then
  PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
  PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
  PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)
  if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 11 ]; then
    ok "Python $PY_VER"
  else
    fail "Python $PY_VER found — need >= 3.11"
    ERRORS=$((ERRORS + 1))
  fi
else
  fail "Python 3 not found. Install from https://python.org"
  ERRORS=$((ERRORS + 1))
fi

# Node
if command -v node >/dev/null 2>&1; then
  NODE_VER=$(node --version | sed 's/v//')
  NODE_MAJOR=$(echo "$NODE_VER" | cut -d. -f1)
  if [ "$NODE_MAJOR" -ge 22 ]; then
    ok "Node.js $NODE_VER"
  else
    warn "Node.js $NODE_VER found — HyperFrames needs >= 22. Install from https://nodejs.org"
  fi
else
  warn "Node.js not found. HyperFrames motion graphics will not work."
  warn "Install from https://nodejs.org (LTS version)."
fi

# ffmpeg
if command -v ffmpeg >/dev/null 2>&1; then
  FF_VER=$(ffmpeg -version 2>&1 | head -1 | awk '{print $3}')
  ok "ffmpeg $FF_VER"
else
  fail "ffmpeg not found."
  echo "   Install:"
  echo "     Ubuntu/Debian: sudo apt-get install -y ffmpeg"
  echo "     macOS:         brew install ffmpeg"
  echo "     Arch:          sudo pacman -S ffmpeg"
  ERRORS=$((ERRORS + 1))
fi

# ffprobe
if command -v ffprobe >/dev/null 2>&1; then
  ok "ffprobe"
else
  fail "ffprobe not found (usually bundled with ffmpeg)."
  ERRORS=$((ERRORS + 1))
fi

echo ""

# ── 2. Python Dependencies ───────────────────────────────────────────────────

echo "── Installing Python dependencies ────────────────────────────────────"

if command -v uv >/dev/null 2>&1; then
  uv pip install -e . --quiet && ok "Python deps installed (uv)" || { fail "uv install failed"; ERRORS=$((ERRORS + 1)); }
elif command -v pip3 >/dev/null 2>&1; then
  pip3 install -e . --quiet && ok "Python deps installed (pip)" || { fail "pip install failed"; ERRORS=$((ERRORS + 1)); }
else
  fail "No pip/uv found. Install Python first."
  ERRORS=$((ERRORS + 1))
fi

# video-use Python deps
if [ -f "tools/video-use/pyproject.toml" ]; then
  if command -v uv >/dev/null 2>&1; then
    (cd tools/video-use && uv pip install -e . --quiet) && ok "video-use Python deps" || warn "video-use dep install had issues"
  else
    (cd tools/video-use && pip3 install -e . --quiet) && ok "video-use Python deps" || warn "video-use dep install had issues"
  fi
fi

echo ""

# ── 3. Node Dependencies (HyperFrames) ───────────────────────────────────────

echo "── Installing Node dependencies ───────────────────────────────────────"

if command -v npm >/dev/null 2>&1; then
  npm install --silent && ok "Node deps installed (npm)" || { fail "npm install failed"; ERRORS=$((ERRORS + 1)); }
else
  warn "npm not available — skipping Node deps (HyperFrames will not work)"
fi

echo ""

# ── 4. Environment File ───────────────────────────────────────────────────────

echo "── Environment file ───────────────────────────────────────────────────"

if [ ! -f ".env" ]; then
  cp .env.example .env
  warn ".env created from template. Fill in ELEVENLABS_API_KEY before editing."
else
  ok ".env already exists"
fi

if grep -q '^ELEVENLABS_API_KEY=..' .env 2>/dev/null; then
  ok "ELEVENLABS_API_KEY is set"
else
  warn "ELEVENLABS_API_KEY is empty in .env — transcription will not work."
  echo "   Get a key at: https://elevenlabs.io/app/settings/api-keys"
fi

echo ""

# ── 5. Register Skills with Agents ───────────────────────────────────────────

echo "── Registering agent skills ───────────────────────────────────────────"

SKILLS_DIR="$WORKSPACE_ROOT/skills"

# Claude Code
if [ -d "$HOME/.claude" ]; then
  mkdir -p "$HOME/.claude/skills"
  ln -sfn "$WORKSPACE_ROOT" "$HOME/.claude/skills/editing-workspace"
  ok "Skills registered for Claude Code (~/.claude/skills/editing-workspace → workspace)"
else
  warn "Claude Code not detected (~/.claude/ missing). Skipping Claude Code skill registration."
fi

# Codex
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
if [ -d "$CODEX_HOME" ]; then
  mkdir -p "$CODEX_HOME/skills"
  ln -sfn "$WORKSPACE_ROOT" "$CODEX_HOME/skills/editing-workspace"
  ok "Skills registered for Codex ($CODEX_HOME/skills/editing-workspace → workspace)"
else
  warn "Codex not detected ($CODEX_HOME/ missing). Skipping Codex skill registration."
fi

echo ""

# ── 6. Verify Setup ──────────────────────────────────────────────────────────

echo "── Verifying setup ────────────────────────────────────────────────────"

python3 -c "from modules.captions import generator; print('captions OK')" 2>/dev/null \
  && ok "modules.captions imports correctly" \
  || { fail "modules.captions import failed"; ERRORS=$((ERRORS + 1)); }

python3 -c "from modules.timestamps import generate_timestamps; print('timestamps OK')" 2>/dev/null \
  && ok "modules.timestamps imports correctly" \
  || { fail "modules.timestamps import failed"; ERRORS=$((ERRORS + 1)); }

python3 -c "from modules.thumbnails import extractor, composer; print('thumbnails OK')" 2>/dev/null \
  && ok "modules.thumbnails imports correctly" \
  || { fail "modules.thumbnails import failed"; ERRORS=$((ERRORS + 1)); }

python3 -c "from modules.motion_graphics import bridge; print('motion_graphics OK')" 2>/dev/null \
  && ok "modules.motion_graphics imports correctly" \
  || { fail "modules.motion_graphics import failed"; ERRORS=$((ERRORS + 1)); }

if [ -f "tools/video-use/helpers/timeline_view.py" ]; then
  python3 tools/video-use/helpers/timeline_view.py --help >/dev/null 2>&1 \
    && ok "video-use helpers are functional" \
    || warn "video-use helpers had an issue (may need Python deps from tools/video-use)"
fi

echo ""

# ── Summary ──────────────────────────────────────────────────────────────────

if [ "$ERRORS" -eq 0 ]; then
  echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
  echo -e "${GREEN}  ✅ Workspace is ready!${NC}"
  echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
  echo ""
  echo "  Next steps:"
  echo "  1. Fill in your ELEVENLABS_API_KEY in .env"
  echo "  2. Drop raw footage in a folder"
  echo "  3. Run: ./scripts/new-project.sh /path/to/footage"
  echo "  4. Start your agent and say: edit these into a final video"
  echo ""
else
  echo -e "${RED}═══════════════════════════════════════════════════════════${NC}"
  echo -e "${RED}  ❌ Setup completed with $ERRORS error(s). Fix them above.${NC}"
  echo -e "${RED}═══════════════════════════════════════════════════════════${NC}"
  exit 1
fi
