#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required. Install Python 3.10 or newer, then rerun this script."
  exit 1
fi

PYTHON_VERSION_OK="$(python3 - <<'PY'
import sys
print("1" if sys.version_info >= (3, 10) else "0")
PY
)"

if [ "$PYTHON_VERSION_OK" != "1" ]; then
  echo "Python 3.10 or newer is required."
  echo "Found: $(python3 --version)"
  exit 1
fi

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install --editable .

if [ ! -f study/pilot-v1/.env ]; then
  cp study/pilot-v1/.env.example study/pilot-v1/.env
  echo "Created study/pilot-v1/.env from the template."
  echo "Edit study/pilot-v1/.env before running the study."
fi

echo
echo "Install complete."
echo "Next: edit study/pilot-v1/.env, then run:"
echo "  ./study/pilot-v1/run_gum.sh"
