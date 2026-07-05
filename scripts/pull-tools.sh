#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# scripts/pull-tools.sh
# Pull the vendored video-use and HyperFrames tools.
#
# The original design used git subtrees, but git-subtree is not available on
# every machine. This script clones the upstream repos as read-only vendored
# copies. Run it automatically via ./scripts/setup.sh, or manually after clone.
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

WORKSPACE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$WORKSPACE_ROOT"

VIDEO_USE_URL="${VIDEO_USE_URL:-https://github.com/browser-use/video-use.git}"
HYPERFRAMES_URL="${HYPERFRAMES_URL:-https://github.com/heygen-com/hyperframes.git}"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ok()   { echo -e "${GREEN}✅ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
fail() { echo -e "${RED}❌ $1${NC}"; }

pull_repo() {
    local dir="$1"
    local url="$2"

    if [ -d "$dir/.git" ]; then
        echo "── Updating $(basename "$dir") ────────────────────────────────────────────"
        if (cd "$dir" && git pull --depth 1 --rebase); then
            ok "Updated $dir"
        else
            warn "Could not update $dir — re-cloning fresh copy"
            rm -rf "$dir"
            git clone --depth 1 "$url" "$dir" && ok "Re-cloned $dir" || { fail "Failed to clone $dir"; return 1; }
        fi
    else
        echo "── Cloning $(basename "$dir") ─────────────────────────────────────────────"
        rm -rf "$dir"
        git clone --depth 1 "$url" "$dir" && ok "Cloned $dir" || { fail "Failed to clone $dir"; return 1; }
    fi
}

pull_repo "tools/video-use" "$VIDEO_USE_URL"
pull_repo "tools/hyperframes" "$HYPERFRAMES_URL"

echo ""
ok "Vendored tools ready."
