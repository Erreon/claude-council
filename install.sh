#!/bin/bash
# Claude Council - Installation Script
# Installs the council skills for Claude Code

set -e

SKILLS_DIR="$HOME/.claude/skills"
SESSIONS_DIR="$HOME/.claude/council/sessions"
ARCHIVE_DIR="$HOME/Documents/council"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Parse flags
USE_COPY=0
for arg in "$@"; do
    case "$arg" in
        --copy) USE_COPY=1 ;;
        --help|-h)
            echo "Usage: ./install.sh [--copy]"
            echo ""
            echo "Options:"
            echo "  --copy    Copy files instead of symlinking (default: symlink)"
            echo ""
            echo "Symlink mode (default) keeps installed skills linked to this repo,"
            echo "so edits in either location are automatically reflected."
            echo "Use --copy if you don't want to keep the repo cloned in place."
            exit 0
            ;;
    esac
done

echo "=== Claude Council Installer ==="
echo ""

if [ "$USE_COPY" -eq 1 ]; then
    echo "Mode: copy (files will be independent of this repo)"
else
    echo "Mode: symlink (edits in either location stay in sync)"
fi
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

# Install skill files (symlink or copy)
install_file() {
    local src="$1"
    local dest="$2"

    # Remove existing file/symlink
    rm -f "$dest"

    if [ "$USE_COPY" -eq 1 ]; then
        cp "$src" "$dest"
    else
        ln -s "$src" "$dest"
    fi
}

echo ""
echo "Installing skills..."

install_file "$SCRIPT_DIR/skills/council/SKILL.md" "$SKILLS_DIR/council/SKILL.md"
install_file "$SCRIPT_DIR/skills/council/council_cli.py" "$SKILLS_DIR/council/council_cli.py"
chmod +x "$SKILLS_DIR/council/council_cli.py" 2>/dev/null || chmod +x "$SCRIPT_DIR/skills/council/council_cli.py"
echo "  [OK] /council (+ CLI helper)"

install_file "$SCRIPT_DIR/skills/council-debate/SKILL.md" "$SKILLS_DIR/council-debate/SKILL.md"
echo "  [OK] /council-debate"

install_file "$SCRIPT_DIR/skills/council-history/SKILL.md" "$SKILLS_DIR/council-history/SKILL.md"
echo "  [OK] /council-history"

# Check Python 3 availability (informational only)
echo ""
echo "Checking optional dependencies..."
if command -v python3 &> /dev/null; then
    PY_VERSION=$(python3 --version 2>&1)
    echo "  [OK] python3 ($PY_VERSION) — CLI helper will be active"
else
    echo "  [INFO] python3 not found — CLI helper will be skipped (council works fine without it)"
fi

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
if [ "$USE_COPY" -eq 0 ]; then
    echo ""
    echo "Skills are symlinked to: $SCRIPT_DIR/skills/"
    echo "Edits in either location will stay in sync."
fi
