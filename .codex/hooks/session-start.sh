#!/usr/bin/env bash
# SessionStart fail-closed per Codex Local e Worktree.

set -uo pipefail

radice="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
output_file="$(mktemp)"
trap 'rm -f "$output_file"' EXIT

if bash "$radice/scripts/setup.sh" >"$output_file" 2>&1; then
    cat "$output_file"
    exit 0
fi

cat "$output_file" >&2
printf '%s\n' \
    '{"continue":false,"stopReason":"Setup del repository fallito.","systemMessage":"Il setup locale non è riuscito: correggere l’ambiente prima di continuare."}'
