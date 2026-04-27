#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# scripts/new-project.sh
# Bootstrap a new video project folder.
# Usage: ./scripts/new-project.sh /path/to/footage
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 /path/to/footage"
  exit 1
fi

FOOTAGE_DIR="$(realpath "$1")"
EDIT_DIR="$FOOTAGE_DIR/edit"
TODAY=$(date '+%Y-%m-%d')

if [ ! -d "$FOOTAGE_DIR" ]; then
  echo "❌ Directory does not exist: $FOOTAGE_DIR"
  exit 1
fi

mkdir -p "$EDIT_DIR/transcripts"
mkdir -p "$EDIT_DIR/animations"
mkdir -p "$EDIT_DIR/clips_graded"
mkdir -p "$EDIT_DIR/verify"

# Create project.md if not exists
if [ ! -f "$EDIT_DIR/project.md" ]; then
  cat > "$EDIT_DIR/project.md" << EOF
---
type: video_project
status: planning
created_date: $TODAY
title: $(basename "$FOOTAGE_DIR")
tags: [video, project]
---

# Project: $(basename "$FOOTAGE_DIR")
Started: $TODAY
Footage: $FOOTAGE_DIR

---

## Session 1 — $TODAY

**Strategy:** (fill in after first conversation with agent)
**Decisions:** —
**Reasoning log:** —
**Outstanding:** —
EOF
  echo "✅ project.md created with Obsidian Frontmatter"
else
  echo "ℹ️  project.md already exists — skipping."
fi

# Handle Obsidian Linking if configured
ENV_FILE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/.env"
if [ -f "$ENV_FILE" ]; then
  # Extract safely
  OBSIDIAN_VAULT=$(grep '^OBSIDIAN_VAULT_PATH=' "$ENV_FILE" | cut -d'=' -f2- | tr -d '"' || true)
  if [ -n "$OBSIDIAN_VAULT" ] && [ -d "$OBSIDIAN_VAULT" ]; then
    VAULT_PROJ_DIR="$OBSIDIAN_VAULT/Video Projects/$(basename "$FOOTAGE_DIR")"
    mkdir -p "$VAULT_PROJ_DIR"
    
    # Symlink the generated .md files specifically, rather than the whole edit dir to avoid heavy mp4s in the vault
    ln -sf "$EDIT_DIR/project.md" "$VAULT_PROJ_DIR/project.md"
    echo "✅ Project securely linked into Obsidian Vault: $VAULT_PROJ_DIR"
  fi
fi

# List source files
echo ""
echo "📁 Footage found in $FOOTAGE_DIR:"
find "$FOOTAGE_DIR" -maxdepth 1 \( -name "*.mp4" -o -name "*.mov" -o -name "*.MP4" -o -name "*.MOV" -o -name "*.mkv" -o -name "*.avi" \) | sort | while read -r f; do
  SIZE=$(du -sh "$f" 2>/dev/null | cut -f1)
  echo "   $SIZE  $(basename "$f")"
done

echo ""
echo "✅ Project scaffolded at: $EDIT_DIR"
echo ""
echo "Next step — tell your agent:"
echo "  Read AGENTS.md at $(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/AGENTS.md,"
echo "  then edit the footage in $FOOTAGE_DIR"
