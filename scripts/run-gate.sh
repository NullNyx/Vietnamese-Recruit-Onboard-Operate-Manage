#!/usr/bin/env bash
# Gate runner: nhan profile, chay lenh tuong ung.
# Usage: run-gate.sh [--allowlist <file>] [--profile <name>] [-- pre_cmd -- post_cmd]
# Xuat JSON report ra stdout.
set -euo pipefail
src_root="$(cd "$(dirname "$0")/.." && pwd)"
allowlist=""
profile="custom"
declare -a extra_cmds=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --allowlist) allowlist="${2:?}"; shift 2 ;;
    --profile) profile="${2:?}"; shift 2 ;;
    --) shift; extra_cmds=("$@"); break ;;
    *) break ;;
  esac
done
report='{"profile":"'"$profile"'","passed":true,"gates":[]}'
cmd_list=()
case "$profile" in
  backend)
    if [[ -n "$allowlist" ]]; then cmd_list+=("$src_root/scripts/check-scope.sh $allowlist"); fi
    cmd_list+=("ruff check ." "mypy ." "pytest -x")
    ;;
  frontend)
    [[ -n "$allowlist" ]] && cmd_list+=("$src_root/scripts/check-scope.sh $allowlist")
    cmd_list+=("npm run lint" "npm run test" "npm run build")
    ;;
  full-stack)
    [[ -n "$allowlist" ]] && cmd_list+=("$src_root/scripts/check-scope.sh $allowlist")
    cmd_list+=("ruff check ." "mypy ." "pytest -x" "npm run lint" "npm run test" "npm run build")
    ;;
  *)
    [[ -n "$allowlist" ]] && cmd_list+=("$src_root/scripts/check-scope.sh $allowlist")
    ;;
esac
for c in "${extra_cmds[@]}"; do cmd_list+=("$c"); done
for cmd in "${cmd_list[@]}"; do
  label="${cmd%% *}"
  set +e
  eval "$cmd" >/tmp/run-gate.out 2>&1
  rc=$?
  set -e
  gate="{\"name\":\"$label\",\"passed\":$([ $rc -eq 0 ] && echo true || echo false),\"exitCode\":$rc}"
  report="$(echo "$report" | jq -c --argjson g "$gate" '.gates += [$g] | if $g.passed == false then .passed = false else . end')"
done
echo "$report" | jq .
if [[ "$(echo "$report" | jq -r '.passed')" == "true" ]]; then
  exit 0
fi
exit 1
