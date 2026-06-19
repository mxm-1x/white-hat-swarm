#!/usr/bin/env bash
# Launch all four swarm agents, each as its own long-running process.
# Logs go to logs/<agent>.log; Ctrl+C stops them all.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p logs

# Agents import sibling modules (swarm_tools, llm) from agents/, so run there.
export PYTHONPATH="$PWD/agents:${PYTHONPATH:-}"

pids=()
for a in hacker engineer qa_tester compliance; do
  echo "Starting $a ..."
  uv run python "agents/$a.py" >"logs/$a.log" 2>&1 &
  pids+=($!)
  sleep 1
done

echo
echo "All 4 agents running. Tailing logs (Ctrl+C to stop everything)."
echo "  hacker=${pids[0]} engineer=${pids[1]} qa_tester=${pids[2]} compliance=${pids[3]}"
echo
trap 'echo; echo "Stopping..."; kill ${pids[*]} 2>/dev/null || true; exit 0' INT TERM
tail -f logs/hacker.log logs/engineer.log logs/qa_tester.log logs/compliance.log
