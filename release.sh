#!/usr/bin/env bash
set -euo pipefail

# release.sh — Bump version in both plugin manifests, commit, tag, and push.
#
# Usage:
#   ./release.sh <version>              # e.g. ./release.sh 1.3.0
#   ./release.sh patch|minor|major      # auto-increment from current version
#   ./release.sh <version> --push       # bump and push without prompting

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_JSON="$REPO_DIR/.claude-plugin/plugin.json"
MARKETPLACE_JSON="$REPO_DIR/.claude-plugin/marketplace.json"

AUTO_PUSH=false
if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "Usage: $0 <version|patch|minor|major> [--push]"
  echo ""
  echo "Examples:"
  echo "  $0 1.3.0    # set explicit version"
  echo "  $0 patch    # 1.2.0 -> 1.2.1"
  echo "  $0 minor    # 1.2.0 -> 1.3.0"
  echo "  $0 major    # 1.2.0 -> 2.0.0"
  echo "  $0 patch --push  # bump and push without prompting"
  exit 1
fi

if [[ $# -eq 2 && "$2" == "--push" ]]; then
  AUTO_PUSH=true
elif [[ $# -eq 2 ]]; then
  echo "Error: Unknown flag '$2' (did you mean --push?)"
  exit 1
fi

# Read current version from plugin.json
CURRENT=$(grep -o '"version": *"[^"]*"' "$PLUGIN_JSON" | head -1 | sed 's/.*"\([0-9][0-9.]*\)".*/\1/')
if [[ -z "$CURRENT" ]]; then
  echo "Error: Could not read current version from $PLUGIN_JSON"
  exit 1
fi

IFS='.' read -r CUR_MAJOR CUR_MINOR CUR_PATCH <<< "$CURRENT"

case "$1" in
  patch) NEW_VERSION="$CUR_MAJOR.$CUR_MINOR.$((CUR_PATCH + 1))" ;;
  minor) NEW_VERSION="$CUR_MAJOR.$((CUR_MINOR + 1)).0" ;;
  major) NEW_VERSION="$((CUR_MAJOR + 1)).0.0" ;;
  *)
    if [[ ! "$1" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
      echo "Error: Version must be semver (e.g. 1.3.0) or patch|minor|major"
      exit 1
    fi
    NEW_VERSION="$1"
    ;;
esac

if [[ "$NEW_VERSION" == "$CURRENT" ]]; then
  echo "Version is already $CURRENT — nothing to do."
  exit 0
fi

echo "Bumping version: $CURRENT -> $NEW_VERSION"

# Update both manifest files (macOS-compatible sed)
sed -i '' "s/\"version\": *\"$CURRENT\"/\"version\": \"$NEW_VERSION\"/" "$PLUGIN_JSON"
sed -i '' "s/\"version\": *\"$CURRENT\"/\"version\": \"$NEW_VERSION\"/" "$MARKETPLACE_JSON"

# Verify the update worked
VERIFY_PLUGIN=$(grep -o '"version": *"[^"]*"' "$PLUGIN_JSON" | head -1)
VERIFY_MARKETPLACE=$(grep -o '"version": *"[^"]*"' "$MARKETPLACE_JSON" | head -1)

echo "  plugin.json:      $VERIFY_PLUGIN"
echo "  marketplace.json: $VERIFY_MARKETPLACE"

# Stage, commit, tag, push
cd "$REPO_DIR"
git add .claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "release: v$NEW_VERSION"
git tag "v$NEW_VERSION"

echo ""
echo "Committed and tagged v$NEW_VERSION."
echo ""

if [[ "$AUTO_PUSH" == true ]]; then
  git push origin main --tags
  echo "Pushed. Users can now run: claude plugin update claude-council@claude-council"
elif [[ -t 0 ]]; then
  read -rp "Push to origin? [Y/n] " PUSH
  PUSH="${PUSH:-Y}"
  if [[ "$PUSH" =~ ^[Yy]$ ]]; then
    git push origin main --tags
    echo "Pushed. Users can now run: claude plugin update claude-council@claude-council"
  else
    echo "Skipped push. Run manually:"
    echo "  git push origin main --tags"
  fi
else
  echo "Non-interactive shell detected. Run manually or use --push:"
  echo "  git push origin main --tags"
fi
