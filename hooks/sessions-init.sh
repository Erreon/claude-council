#!/bin/bash
# Ensure council session and archive directories exist.
# Runs on SessionStart via plugin hooks — silent no-op if dirs already exist.
mkdir -p "$HOME/.claude/council/sessions"
mkdir -p "$HOME/Documents/council"

# Ensure CLI helper is discoverable at the standard path (~/.claude/skills/council/).
# When installed as a plugin, the CLI lives in the plugin cache. CLAUDE_PLUGIN_ROOT
# is set by the plugin system when running hooks; fall back to BASH_SOURCE for manual runs.
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." && pwd)}"
CLI_SRC="$PLUGIN_ROOT/skills/council/council_cli.py"
CLI_DEST="$HOME/.claude/skills/council/council_cli.py"

if [ -f "$CLI_SRC" ] && [ ! -f "$CLI_DEST" ]; then
    mkdir -p "$(dirname "$CLI_DEST")"
    ln -sf "$CLI_SRC" "$CLI_DEST"
fi
