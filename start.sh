#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [[ -z "${DISPLAY:-}" ]]; then
    echo "HOST requires an X11 display. Wayland-only sessions are not supported."
    exit 1
fi

python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
exec .venv/bin/python etero_owner_selection.py
