#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

"$PROJECT_DIR/.venv/bin/pip" install --upgrade pip
"$PROJECT_DIR/.venv/bin/pip" install -r requirements.txt

echo "Virtualenv ready at $PROJECT_DIR/.venv"
echo "Run initial setup: $PROJECT_DIR/.venv/bin/python $PROJECT_DIR/main.py --configure-only"
