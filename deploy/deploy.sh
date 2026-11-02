#!/usr/bin/env bash
# Runs ON the Droplet as the deploy user, from /srv/labourlens/deploy. Used by the GitHub Actions deploy job and by hand.
#
#   ./deploy.sh up <image-tag>   pull and start that tag; if it does not become healthy, return to the previous tag
#   ./deploy.sh rollback         start the previous tag again
#   ./deploy.sh restart          recreate all containers on the current tag (reloads .env and the corpus; the kill switch)
#   ./deploy.sh logs [service] [lines]   app (default), caddy or mcp
#   ./deploy.sh status           show the current/previous tag, containers and /healthz
#
# State: /srv/labourlens/state/{current_tag,previous_tag}. Secrets are read by compose from /srv/labourlens/.env; this
# script never prints them.
# Set LABOURLENS_IMAGE in that private .env to YOUR lower-case GHCR repository; this script selects only IMAGE_TAG.
set -euo pipefail

root=/srv/labourlens
state="$root/state"
[ -f "$root/.env" ] || { echo "missing $root/.env (see docs/deploy.md)" >&2; exit 1; }
cd "$root/deploy"
mkdir -p "$state"

compose() {
  local profiles=()
  [ -f "$root/mcp.env" ] && profiles=(--profile mcp)
  docker compose --env-file "$root/.env" "${profiles[@]}" "$@"
}

read_tag() { [ -f "$state/$1" ] && cat "$state/$1" || true; }

valid_tag() { [[ "$1" =~ ^[A-Za-z0-9_.-]{1,128}$ ]]; }

domain() { grep -E '^DOMAIN=' "$root/.env" | head -1 | cut -d= -f2- | tr -d '"' | tr -d "'"; }

start() { # tag -> 0 if app and Caddy come up healthy and the public edge answers /healthz
  local tag="$1"
  export IMAGE_TAG="$tag"
  compose up -d --remove-orphans --wait --wait-timeout 240 || return 1
  local d
  d="$(domain)"
  for _ in $(seq 1 12); do
    if curl -fsS --max-time 8 --resolve "$d:443:127.0.0.1" "https://$d/healthz" >/dev/null 2>&1; then
      echo "edge healthy: https://$d/healthz answered (tag $tag)"
      return 0
    fi
    sleep 5
  done
  echo "edge check failed: https://$d/healthz did not answer through Caddy" >&2
  return 1
}

case "${1:-}" in
  up)
    tag="${2:-}"; valid_tag "$tag" || { echo "usage: $0 up <image-tag>" >&2; exit 2; }
    prev="$(read_tag current_tag)"
    export IMAGE_TAG="$tag"
    compose pull --quiet app
    if start "$tag"; then
      [ -n "$prev" ] && [ "$prev" != "$tag" ] && echo "$prev" > "$state/previous_tag"
      echo "$tag" > "$state/current_tag"
      docker image prune -f >/dev/null
      echo "deployed $tag (previous: ${prev:-none})"
    else
      echo "deploy of $tag FAILED" >&2
      compose logs --no-color --tail 40 app >&2 || true
      if [ -n "$prev" ] && [ "$prev" != "$tag" ]; then
        echo "rolling back to $prev" >&2
        if start "$prev"; then echo "rolled back to $prev; $tag is NOT live" >&2; else echo "rollback to $prev also failed" >&2; fi
      else
        echo "no previous tag to roll back to" >&2
      fi
      exit 1
    fi
    ;;
  rollback)
    prev="$(read_tag previous_tag)"; cur="$(read_tag current_tag)"
    [ -n "$prev" ] || { echo "no previous tag recorded" >&2; exit 1; }
    start "$prev"
    echo "$cur" > "$state/previous_tag"; echo "$prev" > "$state/current_tag"
    echo "rolled back to $prev"
    ;;
  restart)
    cur="$(read_tag current_tag)"; [ -n "$cur" ] || { echo "no current tag recorded" >&2; exit 1; }
    export IMAGE_TAG="$cur"
    compose up -d --force-recreate --remove-orphans --wait --wait-timeout 240
    ;;
  logs)
    IMAGE_TAG="$(read_tag current_tag)"; export IMAGE_TAG="${IMAGE_TAG:-none}"
    compose logs --no-color --tail "${3:-100}" "${2:-app}"
    ;;
  status)
    echo "current:  $(read_tag current_tag)"
    echo "previous: $(read_tag previous_tag)"
    IMAGE_TAG="$(read_tag current_tag)"; export IMAGE_TAG="${IMAGE_TAG:-none}"
    compose ps
    curl -fsS --max-time 8 --resolve "$(domain):443:127.0.0.1" "https://$(domain)/healthz" || echo "(edge /healthz not answering)"
    echo
    ;;
  *) echo "usage: $0 {up <tag>|rollback|restart|logs [service] [lines]|status}" >&2; exit 2 ;;
esac
