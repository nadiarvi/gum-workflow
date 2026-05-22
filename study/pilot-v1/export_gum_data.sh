#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

if [ ! -f study/pilot-v1/.env ]; then
  echo "Missing study/pilot-v1/.env."
  exit 1
fi

set -a
source study/pilot-v1/.env
set +a

DATA_DIR="${GUM_DATA_DIR:-$HOME/.cache/gum}"

if [ ! -d "$DATA_DIR" ]; then
  echo "No GUM data directory found at: $DATA_DIR"
  exit 1
fi

EXPORT_DIR="$ROOT_DIR/study_exports"
mkdir -p "$EXPORT_DIR"

SAFE_USER="$(printf '%s' "${USER_NAME:-participant}" | tr -cs '[:alnum:]' '-' | sed 's/^-//;s/-$//')"
STAMP="$(date +%Y%m%d-%H%M%S)"
ARCHIVE="$EXPORT_DIR/gum-pilot-v1-${SAFE_USER:-participant}-${STAMP}.zip"

(
  cd "$(dirname "$DATA_DIR")"
  zip -r "$ARCHIVE" "$(basename "$DATA_DIR")"
)

echo "Export created:"
echo "$ARCHIVE"
echo
echo "This archive may contain sensitive observations, propositions, screenshots, and workflow data."
