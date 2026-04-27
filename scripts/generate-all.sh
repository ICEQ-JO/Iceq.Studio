#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# scripts/generate-all.sh
# One-shot: generate timestamps, captions, and thumbnail for a completed project.
#
# Prerequisites:
#   - edit/edl.json exists (video is already edited)
#   - edit/final.mp4 exists (video is already rendered)
#   - edit/takes_packed.md exists (transcript is packed)
#
# Usage:
#   ./scripts/generate-all.sh /path/to/footage/edit/
#   ./scripts/generate-all.sh /path/to/footage/edit/ --platform instagram
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

WORKSPACE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ $# -lt 1 ]; then
  echo "Usage: $0 /path/to/footage/edit/ [--platform youtube|instagram|linkedin|twitter|tiktok]"
  exit 1
fi

EDIT_DIR="$(realpath "$1")"
PLATFORM="${2:---platform}"
if [ "$PLATFORM" = "--platform" ]; then
  PLATFORM="youtube"
else
  # strip --platform flag if passed
  PLATFORM="${2#--platform}"
  PLATFORM="${PLATFORM#=}"
  PLATFORM="${3:-youtube}"
fi

echo ""
echo "🎬  generate-all — $(basename "$(dirname "$EDIT_DIR")")"
echo "    Edit dir: $EDIT_DIR"
echo "    Platform: $PLATFORM"
echo ""

# ── Validate ─────────────────────────────────────────────────────────────────

if [ ! -d "$EDIT_DIR" ]; then
  echo "❌ Edit dir not found: $EDIT_DIR"
  exit 1
fi

if [ ! -f "$EDIT_DIR/edl.json" ]; then
  echo "❌ edl.json not found. Run the video-use editing pipeline first."
  exit 1
fi

VIDEO="$EDIT_DIR/final.mp4"
if [ ! -f "$VIDEO" ]; then
  VIDEO="$EDIT_DIR/preview.mp4"
  if [ ! -f "$VIDEO" ]; then
    echo "⚠️  Neither final.mp4 nor preview.mp4 found. Thumbnail generation will be skipped."
    VIDEO=""
  fi
fi

# ── 1. Timestamps ─────────────────────────────────────────────────────────────

echo "── Timestamps ─────────────────────────────────────────────────────────"
python3 -m modules.timestamps generate --edit-dir "$EDIT_DIR" --style youtube \
  && echo "" \
  || echo "⚠️  Timestamps generation failed (check edl.json has 'beat' labels)"

# ── 2. Captions ────────────────────────────────────────────────────────────────

echo "── Captions ($PLATFORM) ─────────────────────────────────────────────────"
python3 -m modules.captions generate \
  --edit-dir "$EDIT_DIR" \
  --platform "$PLATFORM" \
  --n-titles 5 \
  && echo "" \
  || echo "⚠️  Caption generation failed (check .env for API keys)"

# ── 3. Thumbnail ────────────────────────────────────────────────────────────────

if [ -n "$VIDEO" ]; then
  echo "── Thumbnail ──────────────────────────────────────────────────────────"
  # Try to read title from generated title_options.md
  TITLE=""
  if [ -f "$EDIT_DIR/title_options.md" ]; then
    TITLE=$(head -1 "$EDIT_DIR/title_options.md" | sed 's/^[0-9]\+\. //')
  fi
  TITLE="${TITLE:-My Video}"

  python3 -m modules.thumbnails generate \
    --video "$VIDEO" \
    --edit-dir "$EDIT_DIR" \
    --title "$TITLE" \
    --method pil \
    && echo "" \
    || echo "⚠️  Thumbnail generation failed (check Pillow is installed)"
fi

# ── 4. Obsidian Sync ────────────────────────────────────────────────────────────

echo "── Obsidian Sync ──────────────────────────────────────────────────────"
if [ -f "$EDIT_DIR/takes_packed.md" ]; then
  # Inject frontmatter if it doesn't exist
  if ! grep -q '^type: transcript' "$EDIT_DIR/takes_packed.md"; then
    TMP_TRANSCRIPT=$(mktemp)
    cat > "$TMP_TRANSCRIPT" << EOF
---
type: transcript
status: completed
date: $(date '+%Y-%m-%d')
tags: [video/transcript]
---
EOF
    cat "$EDIT_DIR/takes_packed.md" >> "$TMP_TRANSCRIPT"
    mv "$TMP_TRANSCRIPT" "$EDIT_DIR/takes_packed.md"
    echo "  ✅ Injected Obsidian Frontmatter into takes_packed.md"
  else
    echo "  ℹ️  takes_packed.md already has frontmatter"
  fi
fi

# ── Summary ───────────────────────────────────────────────────────────────────

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  ✅ generate-all complete"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "  Outputs in $EDIT_DIR:"
[ -f "$EDIT_DIR/timestamps.md" ]      && echo "  ✅ timestamps.md"      || echo "  ⬜ timestamps.md"
[ -f "$EDIT_DIR/title_options.md" ]   && echo "  ✅ title_options.md"   || echo "  ⬜ title_options.md"
[ -f "$EDIT_DIR/description.md" ]     && echo "  ✅ description.md"     || echo "  ⬜ description.md"
[ -f "$EDIT_DIR/caption_${PLATFORM}.md" ] && echo "  ✅ caption_${PLATFORM}.md" || echo "  ⬜ caption_${PLATFORM}.md"
[ -f "$EDIT_DIR/thumbnail.png" ]      && echo "  ✅ thumbnail.png"      || echo "  ⬜ thumbnail.png"
echo ""
