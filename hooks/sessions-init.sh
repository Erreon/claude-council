#!/bin/bash
# Ensure council session and archive directories exist.
# Runs on SessionStart via plugin hooks — silent no-op if dirs already exist.
mkdir -p "$HOME/.claude/council/sessions"
mkdir -p "$HOME/Documents/council"
