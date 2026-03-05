#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

ENV_FILE="$ROOT_DIR/.env"
if [ -f "$ENV_FILE" ]; then
  # Export variables from .env into this shell and children
  set -a
  # shellcheck disable=SC1090
  . "$ENV_FILE"
  set +a
fi

cd "$ROOT_DIR"

HAS_NO_BROWSER=false
for arg in "$@"; do
  if [ "$arg" = "--no-browser" ]; then
    HAS_NO_BROWSER=true
    break
  fi
done

if [ "$HAS_NO_BROWSER" = true ]; then
  uv run langgraph dev "$@"
else
  uv run langgraph dev --no-browser "$@"
fi


