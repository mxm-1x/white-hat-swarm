"""Compliance audit seal.

Pulls the Band room transcript via the Agent REST API and packages it into a
tamper-evident JSON manifest: the full message/event log plus a SHA-256 digest
over the canonicalized transcript. Changing any logged byte changes the digest,
which is the "immutable compliance manifest" handed to the human approver.

Usage:
    uv run python audit/seal_audit.py                 # newest chat, 'compliance' key
    uv run python audit/seal_audit.py --chat <id>
    uv run python audit/seal_audit.py --agent hacker  # use a different config key

Auth: uses X-API-Key from agent_config.yaml (the named agent). Note: an agent
only sees messages it sent or was @mentioned in, so seal with the agent that was
in the loop longest (Compliance is mentioned last and sees the verdict chain).
"""

import argparse
import hashlib
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "agent_config.yaml"
OUT_DIR = ROOT / "audit"
BASE = "https://app.band.ai/api/v1/agent"


def load_key(agent_key: str) -> str:
    data = yaml.safe_load(CONFIG.read_text())
    if agent_key not in data:
        sys.exit(f"'{agent_key}' not found in agent_config.yaml. Have: {list(data)}")
    return data[agent_key]["api_key"]


def get(path: str, api_key: str):
    req = urllib.request.Request(f"{BASE}{path}", headers={"X-API-Key": api_key})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code} on {path}: {e.read().decode()[:300]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", default="compliance", help="agent_config.yaml key to authenticate as")
    ap.add_argument("--chat", default=None, help="chat/room id (default: newest chat)")
    args = ap.parse_args()

    api_key = load_key(args.agent)

    chats = get("/chats", api_key)
    chat_list = chats.get("data", chats) if isinstance(chats, dict) else chats
    if not chat_list:
        sys.exit("No chats visible to this agent. Make sure it was added to the room.")

    chat_id = args.chat or (chat_list[0].get("id") or chat_list[0].get("chat_id"))
    print(f"Sealing chat: {chat_id}")

    context = get(f"/chats/{chat_id}/context", api_key)
    try:
        participants = get(f"/chats/{chat_id}/participants", api_key)
    except SystemExit:
        participants = None

    transcript_bytes = json.dumps(context, sort_keys=True, separators=(",", ":")).encode()
    digest = hashlib.sha256(transcript_bytes).hexdigest()
    ts = datetime.now(timezone.utc).isoformat()

    manifest = {
        "manifest_version": "1.0",
        "system": "White-Hat Autonomous Remediation Swarm",
        "track": "Track 3 — Regulated & High-Stakes Workflows",
        "chat_id": chat_id,
        "sealed_at_utc": ts,
        "sealed_by_agent": args.agent,
        "policy_reference": "shared/security_policy.md (SOC2 CC6.1/CC7.1/CC7.2, OWASP A03/A09)",
        "participants": participants,
        "transcript": context,
        "integrity": {
            "algorithm": "SHA-256",
            "digest": digest,
            "note": "Digest is computed over the canonicalized transcript. Any change to the log invalidates it.",
        },
        "human_approval": {
            "status": "PENDING",
            "approver": None,
            "decision_at_utc": None,
        },
    }

    OUT_DIR.mkdir(exist_ok=True)
    out = OUT_DIR / f"audit_seal_{chat_id}.json"
    out.write_text(json.dumps(manifest, indent=2))

    print(f"\n✅ Sealed audit manifest -> {out}")
    print(f"   SHA-256: {digest}")
    print(f"   Sealed at: {ts}")
    print("   Human approval: PENDING (awaiting gatekeeper sign-off)")


if __name__ == "__main__":
    main()
