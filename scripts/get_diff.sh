#!/usr/bin/env bash
# Print changed files and diff for Requirement Flow.
#
# Usage:
#   get_diff.sh [--base-branch main] [--diff-range HEAD~1..HEAD]

set -euo pipefail

BASE_BRANCH="main"
DIFF_RANGE_OVERRIDE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --base-branch) BASE_BRANCH="$2"; shift 2 ;;
    --diff-range) DIFF_RANGE_OVERRIDE="$2"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Not inside a git worktree" >&2
  exit 1
fi

if [[ -n "$DIFF_RANGE_OVERRIDE" ]]; then
  DIFF_RANGE="$DIFF_RANGE_OVERRIDE"
else
  if git rev-parse "origin/$BASE_BRANCH" >/dev/null 2>&1; then
    REF="origin/$BASE_BRANCH"
  elif git rev-parse "$BASE_BRANCH" >/dev/null 2>&1; then
    REF="$BASE_BRANCH"
  elif git rev-parse origin/master >/dev/null 2>&1; then
    REF="origin/master"
  elif git rev-parse master >/dev/null 2>&1; then
    REF="master"
  else
    DIFF_RANGE="HEAD~1..HEAD"
    REF=""
  fi

  if [[ -n "${REF:-}" ]]; then
    MERGE_BASE=$(git merge-base HEAD "$REF" 2>/dev/null || true)
    if [[ -n "$MERGE_BASE" && "$MERGE_BASE" != "$(git rev-parse HEAD 2>/dev/null)" ]]; then
      DIFF_RANGE="$MERGE_BASE..HEAD"
    else
      DIFF_RANGE="HEAD~1..HEAD"
    fi
  fi
fi

COMMITTED_FILES=$(git diff --name-only "$DIFF_RANGE" 2>/dev/null || true)
UNCOMMITTED_FILES=$(
  { git diff --name-only HEAD; git diff --name-only --cached HEAD; } 2>/dev/null \
    | sort -u || true
)

CHANGED_FILES=$(printf '%s\n%s\n' "$COMMITTED_FILES" "$UNCOMMITTED_FILES" | sort -u | grep -v '^$' || true)

if [[ -z "$CHANGED_FILES" ]]; then
  echo "No changed files detected"
  exit 0
fi

echo "=== Changed Files ==="
echo "$CHANGED_FILES"
echo
echo "=== Diff ==="
echo

for file in $CHANGED_FILES; do
  echo "--- $file ---"
  git diff "$DIFF_RANGE" -- "$file" 2>/dev/null || true
  git diff HEAD -- "$file" 2>/dev/null || true
  echo
done
