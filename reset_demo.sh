#!/usr/bin/env bash
# Restore the planted vulnerability so you can re-run the demo from scratch.
set -euo pipefail
cd "$(dirname "$0")"
cp shared/app_vulnerable.py target_repo/app.py
echo "target_repo/app.py restored (vulnerability re-planted)."
echo "Verifying the suite now FAILS on the vulnerability (expect 1 failed):"
( cd target_repo && PYTHONPATH=. uv run pytest -q ) || true
