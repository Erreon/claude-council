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

# First-run prerequisite check — only runs once after install.
SENTINEL="$HOME/.claude/council/.prereqs-checked"
if [ ! -f "$SENTINEL" ]; then
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║              claude-council — First Run Setup               ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""

    # --- Agent CLI detection ---
    CODEX_OK=false; GEMINI_OK=false; CLAUDE_OK=false
    INSTALLED=0; MISSING_LIST=""

    if command -v codex &>/dev/null; then
        CODEX_OK=true; INSTALLED=$((INSTALLED + 1))
    else
        MISSING_LIST="${MISSING_LIST}\n  codex   (OpenAI)    npm install -g @openai/codex"
    fi
    if command -v gemini &>/dev/null; then
        GEMINI_OK=true; INSTALLED=$((INSTALLED + 1))
    else
        MISSING_LIST="${MISSING_LIST}\n  gemini  (Google)    npm install -g @google/gemini-cli"
    fi
    if command -v claude &>/dev/null; then
        CLAUDE_OK=true; INSTALLED=$((INSTALLED + 1))
    else
        MISSING_LIST="${MISSING_LIST}\n  claude  (Anthropic) https://docs.anthropic.com/en/docs/claude-code"
    fi

    echo "Agent CLIs:"
    $CODEX_OK  && echo "  ✓ codex  (OpenAI)"    || echo "  ✗ codex  (OpenAI)    — not found"
    $GEMINI_OK && echo "  ✓ gemini (Google)"     || echo "  ✗ gemini (Google)    — not found"
    $CLAUDE_OK && echo "  ✓ claude (Anthropic)"  || echo "  ✗ claude (Anthropic) — not found"
    echo ""

    if [ "$INSTALLED" -eq 3 ]; then
        echo "Mode: All 3 agents available — full multi-provider council ready."
    elif [ "$INSTALLED" -eq 0 ]; then
        echo "Mode: No agent CLIs found. Install at least one to use the council."
        printf "\nInstall commands:%b\n" "$MISSING_LIST"
    elif $CLAUDE_OK && [ "$INSTALLED" -eq 1 ]; then
        echo "Mode: Claude-only — the council will auto-dispatch all 3 seats to Claude."
        echo "      (No manual config change needed; /council detects this automatically.)"
        printf "\nTo enable multi-provider, install:%b\n" "$MISSING_LIST"
    else
        echo "Mode: Partial ($INSTALLED of 3) — the council will use what's available and skip the rest."
        printf "\nTo install missing agents:%b\n" "$MISSING_LIST"
    fi
    echo ""

    # --- Python & CLI helper ---
    if command -v python3 &>/dev/null; then
        echo "Python: ✓ $(python3 --version 2>&1)"
    else
        echo "Python: ✗ python3 not found (CLI helper won't work, but skills still function)"
    fi

    if [ -f "$CLI_DEST" ] || [ -f "$CLI_SRC" ]; then
        echo "CLI Helper: ✓ Active"
    else
        echo "CLI Helper: ✗ Not found (skills still work, just slower)"
    fi
    echo ""

    # --- Permissions guidance ---
    echo "⚠  Permissions (DO THIS NOW to avoid prompts on every /council use):"
    echo ""
    echo "  Without these rules, Claude Code will ask \"Do you want to proceed?\""
    echo "  every time you run /council. Add to ~/.claude/settings.json:"
    echo ""
    echo '  {                                          '
    echo '    "permissions": {                          '
    echo '      "allow": [                             '
    echo '        "Bash(python3:*)",                   '
    echo '        "Bash(codex:*)",                     '
    echo '        "Bash(gemini:*)",                    '
    echo '        "Bash(claude:*)",                    '
    echo '        "Bash(echo:*)",                      '
    echo '        "Bash(find:*)",                      '
    echo '        "Bash(command:*)",                   '
    echo '        "Bash(mkdir:*)"                      '
    echo '      ]                                      '
    echo '    }                                        '
    echo '  }                                          '
    echo ""

    # --- Quick reference ---
    echo "Commands:"
    echo "  /council <question>          — Get 3 AI perspectives on any decision"
    echo "  /council-debate <topic>      — Structured adversarial debate"
    echo "  /council-history             — Browse, recap, or archive past sessions"
    echo "  /rate <1-5>                  — Rate a council session"
    echo "  /council-outcome <status>    — Track what happened after following advice"
    echo ""
    echo "Diagnostics:"
    echo "  python3 \"$CLI_SRC\" doctor   — Full health check (versions, dirs, helpers)"
    echo "  python3 \"$CLI_SRC\" agents   — Quick agent availability check"
    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo ""

    mkdir -p "$(dirname "$SENTINEL")"
    touch "$SENTINEL"
fi
