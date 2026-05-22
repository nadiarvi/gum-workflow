#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

if [ ! -f .venv/bin/activate ]; then
  echo "Missing .venv. Run ./study/pilot-v1/install.sh first."
  exit 1
fi

if [ ! -f study/pilot-v1/.env ]; then
  echo "Missing study/pilot-v1/.env."
  exit 1
fi

set -a
source study/pilot-v1/.env
set +a

source .venv/bin/activate

gum --data-directory "${GUM_DATA_DIR:-$HOME/.cache/gum}" --reset-cache
