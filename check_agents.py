"""Verify each agent's Band credentials by calling GET /agent/me.

Run after filling agent_config.yaml:  uv run python check_agents.py
A 200 with the agent's name = good. 401/403 = wrong/expired key.
"""

import sys
import urllib.error
import urllib.request
import json
from pathlib import Path

import yaml

CONFIG = Path(__file__).resolve().parent / "agent_config.yaml"
BASE = "https://app.band.ai/api/v1/agent"

data = yaml.safe_load(CONFIG.read_text())
ok = True
for key, creds in data.items():
    api_key = str(creds.get("api_key", ""))
    if "PASTE" in api_key or not api_key:
        print(f"⚠️  {key:11s} — no API key filled in yet")
        ok = False
        continue
    req = urllib.request.Request(
        f"{BASE}/me",
        headers={
            "X-API-Key": api_key,
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            me = json.loads(r.read().decode())
        name = me.get("name") or me.get("data", {}).get("name") or "(connected)"
        print(f"✅ {key:11s} — authenticated as '{name}'")
    except urllib.error.HTTPError as e:
        print(f"❌ {key:11s} — HTTP {e.code}: {e.read().decode()[:120]}")
        ok = False
    except Exception as e:
        print(f"❌ {key:11s} — {e}")
        ok = False

sys.exit(0 if ok else 1)
