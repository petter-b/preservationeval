#!/usr/bin/env bash
set -euo pipefail

# prep-release.sh — Stamp CHANGELOG.md for a release and push to PR branch.
#
# Usage: scripts/prep-release.sh patch|minor|major
#
# Prerequisites:
#   - Must be on a feature branch (not main)
#   - Clean working tree
#   - gh CLI installed and authenticated

usage() {
  echo "Usage: $0 patch|minor|major"
  exit 1
}

# --- Args ---
[[ $# -eq 1 ]] || usage
BUMP_TYPE="$1"
case "$BUMP_TYPE" in
  patch|minor|major) ;;
  *) usage ;;
esac

# --- Safety checks ---
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [[ "$CURRENT_BRANCH" == "main" || "$CURRENT_BRANCH" == "master" ]]; then
  echo "Error: cannot run on '$CURRENT_BRANCH'. Switch to a feature branch first."
  exit 1
fi

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "Error: working tree is not clean. Commit or stash changes first."
  exit 1
fi

if ! command -v gh &>/dev/null; then
  echo "Error: gh CLI not found. Install it: https://cli.github.com/"
  exit 1
fi

# --- Version computation (pure bash) ---
LATEST_TAG=$(git describe --tags --abbrev=0 --match="v*" 2>/dev/null || echo "v0.0.0")
VERSION="${LATEST_TAG#v}"
IFS='.' read -r v_major v_minor v_patch <<< "$VERSION"

case "$BUMP_TYPE" in
  patch)
    v_patch=$((v_patch + 1))
    ;;
  minor)
    v_minor=$((v_minor + 1))
    v_patch=0
    ;;
  major)
    v_major=$((v_major + 1))
    v_minor=0
    v_patch=0
    ;;
esac

NEW_VERSION="${v_major}.${v_minor}.${v_patch}"
echo "Version: ${VERSION} → ${NEW_VERSION}"

# --- Label PR (best-effort) ---
label_pr() {
  if gh pr view "$CURRENT_BRANCH" &>/dev/null; then
    gh pr edit --add-label "release-${BUMP_TYPE}"
    echo "Labeled PR with release-${BUMP_TYPE}."
  else
    echo "Warning: no open PR found for ${CURRENT_BRANCH}. Label manually if needed."
  fi
}

# --- Idempotency: skip if already stamped ---
if grep -q "^## \[${NEW_VERSION}\]" CHANGELOG.md; then
  echo "Warning: CHANGELOG.md already contains [${NEW_VERSION}]. Skipping stamp."
  label_pr
  echo "Done. Release ${NEW_VERSION} is ready for CI."
  exit 0
fi

# --- Validate [Unreleased] section exists and has entries ---
if ! grep -q '^## \[Unreleased\]' CHANGELOG.md; then
  echo "Error: CHANGELOG.md is missing an [Unreleased] section."
  exit 1
fi

ENTRY_COUNT=$(awk '/^## \[Unreleased\]/{found=1; next} /^## \[/{found=0} found && /^[[:space:]]*- /{count++} END{print count+0}' CHANGELOG.md)
if [[ "$ENTRY_COUNT" -eq 0 ]]; then
  echo "Error: [Unreleased] section has no entries. Document your changes first."
  exit 1
fi
echo "Found ${ENTRY_COUNT} unreleased entries."

# --- Stamp CHANGELOG ---
RELEASE_DATE=$(date -u +%Y-%m-%d)

# macOS sed requires '' after -i; Linux does not.
# Use a temp file for portability.
TMPFILE=$(mktemp)
awk -v ver="$NEW_VERSION" -v date="$RELEASE_DATE" '
  /^## \[Unreleased\]/ {
    print $0
    print ""
    print "## [" ver "] - " date
    next
  }
  { print }
' CHANGELOG.md > "$TMPFILE"
mv "$TMPFILE" CHANGELOG.md

# --- Verify stamp took effect ---
if ! grep -q "^## \[${NEW_VERSION}\] - ${RELEASE_DATE}$" CHANGELOG.md; then
  echo "Error: CHANGELOG stamp failed — [${NEW_VERSION}] not found after transform."
  exit 1
fi
echo "Stamped CHANGELOG.md: [${NEW_VERSION}] - ${RELEASE_DATE}"

# --- Commit and push ---
git add CHANGELOG.md
git commit -m "chore: prepare changelog for release ${NEW_VERSION}"
git push origin "$CURRENT_BRANCH"
echo "Pushed to ${CURRENT_BRANCH}."

label_pr
echo "Done. Release ${NEW_VERSION} is ready for CI."
