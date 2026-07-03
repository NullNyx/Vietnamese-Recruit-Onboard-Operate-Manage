#!/usr/bin/env bash
set -euo pipefail
src_root="$(cd "$(dirname "$0")/.." && pwd)"
notes_active="$src_root/docs/notes/active"
index_file="$src_root/docs/notes/INDEX.md"
topic="${1:?topic required}"
scope="${2:?scope required}"
shift 2
content="${*:-}"
mkdir -p "$notes_active"
note_file="$notes_active/${topic}.md"
timestamp="$(date +%Y-%m-%d)"
{
  printf '# %s\n\n' "$topic"
  printf '**status:** active\n'
  printf '**scope:** %s\n' "$scope"
  printf '**last_reviewed:** %s\n\n' "$timestamp"
  printf '%s\n' "$content"
} > "$note_file"
if grep -qF -- "- \`$topic\`" "$index_file" 2>/dev/null; then
  :
else
  sed -i '/^## Active$/a\- `'"$topic"'` — scope: '"$scope"' (active, '"$timestamp"')' "$index_file"
fi
echo "note: $note_file"
