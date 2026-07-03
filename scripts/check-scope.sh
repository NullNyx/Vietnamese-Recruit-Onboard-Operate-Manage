#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
allowlist_file="${1:?cần file allowlist}"

if [[ ! -f "$allowlist_file" ]]; then
  echo "LOI: khong tim thay allowlist: $allowlist_file" >&2
  exit 1
fi

cd "$repo_root"

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "SKIP: khong phai git repo"
  exit 0
fi

changed="$(git diff --name-only --cached --diff-filter=ACMR 2>/dev/null || true)"
if [[ -z "$changed" ]]; then
  changed="$(git diff --name-only --diff-filter=ACMR 2>/dev/null || true)"
fi

violations=()
while IFS= read -r file; do
  [[ -z "$file" ]] && continue
  ok=false
  while IFS= read -r rule; do
    [[ -z "$rule" || "$rule" == \#* ]] && continue
    if [[ "$rule" == */ ]]; then
      [[ "$file" == "$rule"* ]] && ok=true
    else
      [[ "$file" == "$rule" ]] && ok=true
    fi
    [[ "$ok" == true ]] && break
  done < "$allowlist_file"
  [[ "$ok" == true ]] || violations+=("$file")
done <<< "$changed"

if [[ ${#violations[@]} -gt 0 ]]; then
  printf 'LOI: file ngoai scope:\n' >&2
  printf '%s\n' "${violations[@]}" >&2
  exit 1
fi

echo "PASS: scope ok"
