#!/usr/bin/env bash
#
# Upload the averyio site to GitHub.
# Pushing to the `main` branch publishes it live at https://averyio.net
# (GitHub Pages serves this repo; the CNAME file points the domain here).
#
# Usage:
#   ./upload.sh                     # commits everything with a default message
#   ./upload.sh "your message"      # commits with your own message
#
set -euo pipefail
cd "$(dirname "$0")"

msg="${1:-Update site}"

# Stage every change (new, edited, deleted files).
git add -A

# Nothing changed? Stop here.
if git diff --cached --quiet; then
  echo "Nothing to upload — no changes since the last upload."
  exit 0
fi

echo "Uploading these changes:"
git diff --cached --stat

git commit -m "$msg"
git push origin main

echo ""
echo "✓ Uploaded. Your site updates at https://averyio.net in about a minute."
