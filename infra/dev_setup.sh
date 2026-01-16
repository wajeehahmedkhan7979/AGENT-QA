#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$SCRIPT_DIR/.."
VENV="$REPO_ROOT/.venv"

if [ ! -d "$VENV" ]; then
  echo "Creating virtualenv at $VENV"
  python -m venv "$VENV"
fi

# shellcheck disable=SC1091
source "$VENV/bin/activate"

REQ="$REPO_ROOT/apps/backend/requirements.txt"
if [ ! -f "$REQ" ]; then
  echo "Requirements file not found: $REQ" >&2
  exit 1
fi

pip install -r "$REQ"

echo "Running backend unit tests"
python -m pytest -q apps/backend/tests

echo "Dev setup complete. Activate venv with: source $VENV/bin/activate"
