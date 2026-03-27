#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKSPACE_DIR="${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}"
SKILL_TARGET_DIR="$WORKSPACE_DIR/skills/openclaw-smart-agent"

echo "[1/4] Installing Python runtime from source"
python -m pip install -e "$ROOT_DIR[dev]"

echo "[2/4] Installing plugin dependencies"
npm --prefix "$ROOT_DIR/plugin" install --no-audit --no-fund

echo "[3/4] Initializing config file"
mkdir -p "$ROOT_DIR/config"
if [[ ! -f "$ROOT_DIR/config/config.yaml" ]]; then
  cp "$ROOT_DIR/config/config.example.yaml" "$ROOT_DIR/config/config.yaml"
fi

echo "[4/4] Copying workspace skill"
mkdir -p "$SKILL_TARGET_DIR"
cp -R "$ROOT_DIR/skills/openclaw-smart-agent/." "$SKILL_TARGET_DIR/"

cat <<EOF

Install complete.

Next steps:
1. Start the runtime:
   openclaw-smart-agent serve --config "$ROOT_DIR/config/config.yaml"
2. Publish the plugin package from "$ROOT_DIR/plugin" to npm or ClawHub, then install it in OpenClaw.
3. Restart your OpenClaw session so the copied workspace skill is loaded.

Override the workspace target with:
  OPENCLAW_WORKSPACE=/path/to/workspace ./scripts/install.sh
EOF
