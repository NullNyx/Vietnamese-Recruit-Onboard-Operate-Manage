#!/usr/bin/env bash
set -euo pipefail

src_root="$(cd "$(dirname "$0")/.." && pwd)"
target_root="$(pwd)"
merge=false
overwrite=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --directory)
      target_root="${2:?can co target directory}"
      shift 2
      ;;
    --merge)
      merge=true
      shift
      ;;
    --overwrite)
      overwrite=true
      shift
      ;;
    --yes)
      shift
      ;;
    *)
      echo "LOI: khong ro flag: $1" >&2
      exit 1
      ;;
  esac
done

target_root="$(cd "$target_root" && pwd)"

copy_file() {
  local src="$1"
  local dest="$2"
  mkdir -p "$(dirname "$dest")"
  if [[ -f "$dest" && "$overwrite" != true ]]; then
    return 0
  fi
  cp "$src" "$dest"
}

append_marked_block() {
  local source="$1"
  local dest="$2"
  local marker_start="# --- just-harness start ---"
  local marker_end="# --- just-harness end ---"

  mkdir -p "$(dirname "$dest")"
  if [[ -f "$dest" ]]; then
    if grep -qF "$marker_start" "$dest"; then
      return 0
    fi
    {
      printf '\n%s\n' "$marker_start"
      cat "$source"
      printf '%s\n' "$marker_end"
    } >> "$dest"
  else
    cp "$source" "$dest"
  fi
}

install_tree() {
  local rel="$1"
  local src="$src_root/$rel"
  local dest="$target_root/$rel"
  if [[ -d "$src" ]]; then
    mkdir -p "$dest"
    while IFS= read -r file; do
      [[ -z "$file" ]] && continue
      local rel_file="${file#"$src_root"/}"
      local rel_dir
      rel_dir="$(dirname "$rel_file")"
      mkdir -p "$target_root/$rel_dir"
      if [[ -f "$target_root/$rel_file" && "$overwrite" != true ]]; then
        continue
      fi
      cp "$file" "$target_root/$rel_file"
    done < <(find "$src" -type f | sort)
  fi
}

copy_file "$src_root/README.md" "$target_root/README.md"
copy_file "$src_root/CONTEXT.md" "$target_root/CONTEXT.md"
if [[ "$merge" == true ]]; then
  append_marked_block "$src_root/AGENTS.md" "$target_root/AGENTS.md"
else
  copy_file "$src_root/AGENTS.md" "$target_root/AGENTS.md"
fi

for rel in \
  docs/HARNESS.md \
  docs/FEATURE_INTAKE.md \
  docs/CONTEXT_RULES.md \
  docs/TEST_MATRIX.md \
  docs/profile/README.md \
  docs/workflow-skills.md \
  docs/templates/README.md \
  docs/matt-pocock-skills.md \
  docs/templates/slice-allowlist.json \
  docs/notes/README.md \
  docs/notes/INDEX.md \
  docs/notes/active \
  docs/notes/archive \
  docs/agents/domain.md \
  docs/agents/issue-tracker.md \
  docs/agents/triage-labels.md \
  docs/agents \
  docs/decisions/README.md \
  scripts/README.md \
  scripts/check-scope.sh \
  scripts/run-gate.sh \
  scripts/record-evidence.sh \
  scripts/record-note.sh \
  scripts/install-harness.sh \
  state/.gitkeep \
  .gitignore \
  .editorconfig \
  docs/release-process.md \
  .gitattributes \

do
  src="$src_root/$rel"
  dest="$target_root/$rel"
  if [[ ! -e "$src" ]]; then
    continue
  fi
  if [[ -d "$src" ]]; then
    mkdir -p "$dest"
    continue
  fi
  if [[ "$rel" == "state/.gitkeep" ]]; then
    mkdir -p "$(dirname "$dest")"
    : > "$dest"
    continue
  fi
  copy_file "$src" "$dest"
done

chmod +x "$target_root/scripts/check-scope.sh" "$target_root/scripts/run-gate.sh" "$target_root/scripts/record-evidence.sh" "$target_root/scripts/record-note.sh" "$target_root/scripts/install-harness.sh"

echo "Da cai just-harness vao $target_root"
