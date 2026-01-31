#!/bin/bash
# Claude Council - Installation Script
# Installs the council skills for Claude Code

set -e

SKILLS_DIR="$HOME/.claude/skills"
SESSIONS_DIR="$HOME/.claude/council/sessions"
ARCHIVE_DIR="$HOME/Documents/council"

echo "=== Claude Council Installer ==="
echo ""

# Check for required CLI tools
echo "Checking prerequisites..."
echo ""

check_tool() {
    if command -v "$1" &> /dev/null; then
        echo "  [OK] $1"
        return 0
    else
        echo "  [MISSING] $1 - $2"
        return 1
    fi
}

MISSING=0
check_tool "claude" "Install: https://docs.anthropic.com/en/docs/claude-code" || MISSING=1
check_tool "codex" "Install: npm install -g @openai/codex" || MISSING=1
check_tool "gemini" "Install: npm install -g @google/gemini-cli" || MISSING=1

echo ""

if [ "$MISSING" -eq 1 ]; then
    echo "Some CLI tools are missing. The council works best with all three,"
    echo "but will gracefully degrade if one is unavailable."
    echo ""
    read -p "Continue installation anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        exit 1
    fi
fi

# Create directories
echo "Creating directories..."
mkdir -p "$SKILLS_DIR/council"
mkdir -p "$SKILLS_DIR/council-debate"
mkdir -p "$SKILLS_DIR/council-history"
mkdir -p "$SESSIONS_DIR"
mkdir -p "$ARCHIVE_DIR"
echo "  [OK] $SKILLS_DIR/council/"
echo "  [OK] $SKILLS_DIR/council-debate/"
echo "  [OK] $SKILLS_DIR/council-history/"
echo "  [OK] $SESSIONS_DIR"
echo "  [OK] $ARCHIVE_DIR"

# Copy skill files
echo ""
echo "Installing skills..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

cp "$SCRIPT_DIR/skills/council/skill.md" "$SKILLS_DIR/council/skill.md"
echo "  [OK] /council"

cp "$SCRIPT_DIR/skills/council-debate/skill.md" "$SKILLS_DIR/council-debate/skill.md"
echo "  [OK] /council-debate"

cp "$SCRIPT_DIR/skills/council-history/skill.md" "$SKILLS_DIR/council-history/skill.md"
echo "  [OK] /council-history"

echo ""
echo "=== Installation complete ==="
echo ""
echo "Available commands in Claude Code:"
echo "  /council [question]                        Ask the council"
echo "  /council --personas \"X, Y, Z\" [question]   Ask with specific personas"
echo "  /council-debate [topic]                    Run a structured debate"
echo "  /council-history                           Browse past sessions"
echo ""
echo "Sessions auto-save to: $SESSIONS_DIR"
echo "Archives save to:      $ARCHIVE_DIR"
