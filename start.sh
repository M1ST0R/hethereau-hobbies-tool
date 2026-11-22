#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [[ -z "${DISPLAY:-}" ]]; then
    echo "HHT requires an X11 display. Wayland-only sessions are not supported."
    exit 1
fi

python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
if ! command -v tesseract >/dev/null 2>&1; then
    echo "Tesseract OCR is required. Install it with:"
    echo "  sudo apt install tesseract-ocr tesseract-ocr-eng tesseract-ocr-rus"
    exit 1
fi

exec .venv/bin/python hht_qt_main.py
