#!/usr/bin/env bash
# Proves what Docker would send as build context: builds a FROM-scratch stage that copies the context and exports it to a
# temp directory (nothing is executed), then fails if the corpus, PDFs, secrets or private notes are present.
# Usage: scripts/check-build-context.sh [context-dir]   (default: repository root). Needs Docker with BuildKit.
set -euo pipefail
ctx="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
out="$(mktemp -d)"
trap 'rm -rf "$out"' EXIT

printf 'FROM scratch\nCOPY . /ctx\n' | docker build --quiet --no-cache -f - --output "type=local,dest=$out" "$ctx" >/dev/null

root="$out/ctx"
fail=0
check() { # description, find-args...
  local what="$1"; shift
  local hits
  hits="$(find "$root" "$@" 2>/dev/null | head -5)"
  if [ -n "$hits" ]; then echo "FAIL: $what"; echo "$hits"; fail=1; fi
}
check "top-level data/ is in the build context" -maxdepth 1 -name data
check "private/, study/, experiments/, docs/, artifacts/ or .git in the build context" -maxdepth 1 \( -name private -o -name study -o -name experiments -o -name docs -o -name artifacts -o -name .git \)
check "a PDF is in the build context" -type f -iname '*.pdf'
check "an env file is in the build context" -type f \( -name '.env' -o -name '.env.*' \)
check "corpus file types (parquet, jsonl, npy) are in the build context" -type f \( -name '*.parquet' -o -name '*.jsonl' -o -name '*.npy' \)

if [ "$fail" -ne 0 ]; then exit 1; fi
echo "build context OK: $(find "$root" -type f | wc -l | tr -d ' ') files; top level: $(ls -A "$root" | tr '\n' ' ')"
