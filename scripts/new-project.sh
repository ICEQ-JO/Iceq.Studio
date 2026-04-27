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
  echo "✅ project.md created"
else
  echo "ℹ️  project.md already exists — skipping."
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
