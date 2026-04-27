#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# scripts/link-obsidian.sh
# Link your workspace outputs to an Obsidian Vault
# Usage: ./scripts/link-obsidian.sh "/path/to/Obsidian Vault"
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

WORKSPACE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$WORKSPACE_ROOT/.env"

if [ $# -lt 1 ]; then
  echo "Usage: $0 \"/path/to/Obsidian Vault\""
  echo "Current configuration in .env:"
  grep '^OBSIDIAN_VAULT_PATH=' "$ENV_FILE" 2>/dev/null || echo "  (Not configured)"
  exit 1
fi

VAULT_PATH="$(realpath "$1")"

if [ ! -d "$VAULT_PATH" ]; then
  echo "❌ Error: Directory does not exist: $VAULT_PATH"
  exit 1
fi

if [ ! -d "$VAULT_PATH/.obsidian" ]; then
  echo "⚠️  Warning: $VAULT_PATH does not appear to be an Obsidian Vault (no .obsidian folder)."
  echo "Proceeding anyway..."
fi

# Write it to .env
if grep -q '^OBSIDIAN_VAULT_PATH=' "$ENV_FILE" 2>/dev/null; then
  sed -i "s|^OBSIDIAN_VAULT_PATH=.*|OBSIDIAN_VAULT_PATH=\"$VAULT_PATH\"|" "$ENV_FILE"
else
  echo "" >> "$ENV_FILE"
  echo "OBSIDIAN_VAULT_PATH=\"$VAULT_PATH\"" >> "$ENV_FILE"
fi

# Ensure the Video Projects directory exists in the vault
mkdir -p "$VAULT_PATH/Video Projects"

echo "✅ Linked workspace to Obsidian Vault: $VAULT_PATH"
echo "Future projects created via new-project.sh will automatically sync their text assets here."
