#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

if [ ! -f .venv/bin/activate ]; then
  echo "Missing .venv. Run ./study/pilot-v1/install.sh first."
  exit 1
fi

if [ ! -f study/pilot-v1/.env ]; then
  echo "Missing study/pilot-v1/.env. Copy .env.example to .env and fill it in."
  exit 1
fi

set -a
source study/pilot-v1/.env
set +a

source .venv/bin/activate

echo "Starting GUM for: ${USER_NAME:-unknown participant}"
echo "Data directory: ${GUM_DATA_DIR:-$HOME/.cache/gum}"
echo "Press Ctrl-C to stop."
echo

gum \
  --user-name "${USER_NAME}" \
  --model "${MODEL_NAME:-gpt-4o-mini}" \
  --data-directory "${GUM_DATA_DIR:-$HOME/.cache/gum}" \
  --min-batch-size "${MIN_BATCH_SIZE:-3}" \
  --max-batch-size "${MAX_BATCH_SIZE:-8}"
