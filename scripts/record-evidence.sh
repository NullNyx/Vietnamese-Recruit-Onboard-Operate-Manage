#!/usr/bin/env bash
# evidence recorder: ghi text + JSON
set -euo pipefail
repo_root="$(cd "$(dirname "$0")/.." && pwd)"
label="${1:?label required}"
shift
if [[ "${1:-}" == "--" ]]; then shift; fi
[[ $# -gt 0 ]] || { echo "LOI: can co command" >&2; exit 1; }
mkdir -p "$repo_root/state"
log_file="$repo_root/state/evidence.log"
run_id="$(date +%s)"
json_file="$repo_root/state/evidence-${run_id}.json"
tmp_file="$(mktemp)"
ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
{
  printf '== %s ==\n' "$label"
  printf '$ '
  printf '%q ' "$@"
  printf '\n'
} >> "$log_file"
set +e
"$@" >"$tmp_file" 2>&1
status=$?
set -e
output="$(cat "$tmp_file")"
printf '%s\n' "$output" | tee -a "$log_file"
printf '\n== exit=%s ==\n\n' "$status" | tee -a "$log_file"
jq -n \
  --arg label "$label" \
  --arg ts "$ts" \
  --argjson exit_code "$status" \
  --arg output "$output" \
  '{label:$label,timestamp:$ts,exitCode:$exit_code,output:$output}' > "$json_file"
rm -f "$tmp_file"
exit "$status"
