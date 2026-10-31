#!/usr/bin/env bash
# Copy the minimal runtime data set (deploy/runtime-data.txt, nothing else) from this machine to the Droplet over ssh.
# Dry run by default: it lists what would be transferred. Pass --go to transfer.
#
#   scripts/upload-corpus.sh deploy@203.0.113.10            # dry run
#   scripts/upload-corpus.sh deploy@203.0.113.10 --go       # transfer
#   scripts/upload-corpus.sh deploy@203.0.113.10 --go --with-mcp-snapshots   # also data/snapshots/*.csv for the MCP sidecar
#
# Files land in /srv/labourlens/data (REMOTE_DIR overrides). No --delete: files already on the server are never removed here.
# The MOM passages are not redistributable in public (docs/decisions.md D-001): this goes to your own server over ssh only.
set -euo pipefail

usage() { echo "usage: $0 user@host [--go] [--with-mcp-snapshots]" >&2; exit 2; }
[ $# -ge 1 ] || usage
target="$1"; shift
mode="--dry-run"; snapshots=0
for arg in "$@"; do
  case "$arg" in
    --go) mode="" ;;
    --with-mcp-snapshots) snapshots=1 ;;
    *) usage ;;
  esac
done
case "$target" in *@*) ;; *) usage ;; esac

repo="$(cd "$(dirname "$0")/.." && pwd)"
list="$repo/deploy/runtime-data.txt"
remote_dir="${REMOTE_DIR:-/srv/labourlens/data}"
ssh_opts=(-o BatchMode=yes -o StrictHostKeyChecking=yes)

files="$(mktemp)"
trap 'rm -f "$files"' EXIT
# Strip comments and blank lines, then drop the leading "data/" so paths are relative to the data directory.
grep -v -e '^[[:space:]]*#' -e '^[[:space:]]*$' "$list" | sed 's#^data/##' > "$files"

missing=0
while IFS= read -r f; do
  if [ ! -f "$repo/data/$f" ]; then echo "missing locally: data/$f" >&2; missing=1; fi
done < "$files"
[ "$missing" -eq 0 ] || { echo "refusing to upload: the runtime data set is incomplete on this machine" >&2; exit 1; }

echo "== $(wc -l < "$files" | tr -d ' ') files from deploy/runtime-data.txt -> $target:$remote_dir ${mode:+(DRY RUN, add --go to transfer)}"
# --relative keeps the directory layout. No --chmod (macOS rsync lacks it); permissions are normalised on the server afterwards.
rsync -rltvh --relative $mode -e "ssh ${ssh_opts[*]}" --files-from="$files" "$repo/data/" "$target:$remote_dir/"

if [ "$snapshots" -eq 1 ]; then
  echo "== optional: data/snapshots (*.csv, *.metadata.json) for the MCP sidecar"
  rsync -rltvh $mode -e "ssh ${ssh_opts[*]}" --include='*/' --include='*.csv' --include='*.metadata.json' --exclude='*' "$repo/data/snapshots/" "$target:$remote_dir/snapshots/"
fi
# The app (uid 10001) must be able to write data/audit and the embedding cache; bootstrap sets that ownership once.
if [ -z "$mode" ]; then
  ssh "${ssh_opts[@]}" "$target" "find '$remote_dir' -type d -exec chmod 755 {} + && find '$remote_dir' -type f -exec chmod 644 {} +"
fi
[ -z "$mode" ] && echo "done. Restart the app so it reloads the data: ssh $target 'cd /srv/labourlens/deploy && ./deploy.sh restart'" || true
