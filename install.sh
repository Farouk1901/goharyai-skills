#!/usr/bin/env bash
# Installs the GoharyAI skills into ~/.claude/skills and checks the environment.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
DEST="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
mkdir -p "$DEST"
for s in "$HERE"/skills/goharyai-*; do
  name="$(basename "$s")"
  rm -rf "$DEST/$name"
  cp -R "$s" "$DEST/$name"
  echo "installed $name"
done
cd "$DEST/goharyai-core" && npm install --no-audit --no-fund --silent
node "$DEST/goharyai-core/scripts/run.js" env.py
echo
echo "Done. In Claude Code, try: /goharyai-reel  (or just describe the video you want)."
