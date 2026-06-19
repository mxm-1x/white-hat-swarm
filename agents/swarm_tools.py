"""Shared remediation logic used by all four swarm agents.

These are plain Python functions that operate on the real ``target_repo/`` so
the demo is concrete: the Engineer actually rewrites ``app.py`` and the QA
Tester actually runs ``pytest`` against it (red -> green on screen).

Each agent wraps the relevant functions in its framework's tool format
(LangChain ``@tool`` for LangGraph agents, ``(PydanticModel, fn)`` for CrewAI).
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT / "target_repo"
POLICY = ROOT / "shared" / "security_policy.md"


# --- read / discovery -------------------------------------------------------

def list_repo() -> str:
    files = sorted(p.name for p in REPO.glob("*.py"))
    return "Files in target_repo: " + ", ".join(files)


def read_source(filename: str) -> str:
    path = REPO / Path(filename).name
    if not path.exists():
        return f"ERROR: {filename} not found. Available: {list_repo()}"
    return path.read_text()


def scan_repo() -> str:
    """Cheap static scan for the planted SQL-injection class (CWE-89)."""
    findings = []
    for path in REPO.glob("*.py"):
        if path.name.startswith("test_"):
            continue
        for i, line in enumerate(path.read_text().splitlines(), 1):
            # f-string or % / + concatenation feeding a SQL SELECT/INSERT/...
            if re.search(r"(SELECT|INSERT|UPDATE|DELETE).*", line, re.I) and (
                re.search(r'f["\']', line) or " % " in line or re.search(r'["\']\s*\+', line)
            ):
                findings.append(f"{path.name}:{i}: {line.strip()}")
    if not findings:
        return "No string-built SQL queries found."
    return "POTENTIAL SQL INJECTION (CWE-89 / OWASP A03):\n" + "\n".join(findings)


# --- patching ---------------------------------------------------------------

def apply_patch(filename: str, new_content: str) -> str:
    """Overwrite a source file with the proposed fixed version."""
    path = REPO / Path(filename).name
    if not path.exists():
        return f"ERROR: {filename} not found."
    path.write_text(new_content)
    return f"Patch applied to {path.name} ({len(new_content)} bytes written)."


# --- verification -----------------------------------------------------------

def run_tests() -> str:
    """Run the repo's pytest suite and return a concise pass/fail summary."""
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--no-header"],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        timeout=120,
        env={**os.environ, "PYTHONPATH": str(REPO)},
    )
    out = (proc.stdout + proc.stderr).strip()
    tail = "\n".join(out.splitlines()[-15:])
    verdict = "ALL TESTS PASS ✅" if proc.returncode == 0 else "TESTS FAILED ❌"
    return f"{verdict} (exit={proc.returncode})\n{tail}"


# --- compliance -------------------------------------------------------------

def read_policy() -> str:
    return POLICY.read_text()
