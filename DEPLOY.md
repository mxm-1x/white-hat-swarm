# Deploying the White-Hat Command Center to Render

The app is one Docker web service that runs the FastAPI backend **and** spawns
the four Band agents. A judge opens the URL, clicks **Launch Remediation Swarm**,
watches the agents collaborate live, and clicks **Approve & Deploy** (the human
gate). No Band login needed by the judge.

## Prerequisites
- This repo pushed to GitHub (done: `mxm-1x/white-hat-swarm`).
- **OpenRouter credit added** (https://openrouter.ai/credits, ≥ $10). Without it
  the agents authenticate but can't call the LLM, so nothing happens on Launch.

## Steps
1. Go to https://dashboard.render.com → **New → Blueprint**.
2. Connect the GitHub repo `mxm-1x/white-hat-swarm`. Render reads `render.yaml`.
3. Before the first deploy, set the **secret** env vars (marked `sync: false`).
   Pull the values from your local `agent_config.yaml` and `.env`:

   | Render env var | Value (from your local files) |
   |---|---|
   | `OPENROUTER_API_KEY` | `.env` → OPENROUTER_API_KEY |
   | `HACKER_AGENT_ID` / `HACKER_API_KEY` | `agent_config.yaml` → hacker.agent_id / api_key |
   | `ENGINEER_AGENT_ID` / `ENGINEER_API_KEY` | engineer.* |
   | `QA_TESTER_AGENT_ID` / `QA_TESTER_API_KEY` | qa_tester.* |
   | `COMPLIANCE_AGENT_ID` / `COMPLIANCE_API_KEY` | compliance.* |

   (`LLM_PROVIDER`, `MODEL`, `BAND_*`, `SPAWN_AGENTS` are preset in render.yaml.)
4. Click **Apply / Deploy**. First build takes ~5–10 min (CrewAI is large).
5. When live, open the service URL → that is your **Application URL** for the
   submission. Click **Launch Remediation Swarm**.

## Notes
- **RAM**: 4 agent processes (CrewAI + LangGraph) + API need ~1.5–2 GB. The
  blueprint uses the `standard` (2 GB) plan. `free`/`starter` (512 MB) will OOM.
- **Health check**: `/api/health` returns agent/registry status.
- **Switching LLM**: change `LLM_PROVIDER` (`openrouter|google|groq|openai`) and
  the matching key env var; redeploy.
- **Local run** (same behavior):
  ```bash
  uv run uvicorn server.app:app --port 8000      # spawns agents too
  # open http://localhost:8000
  ```
  Set `SPAWN_AGENTS=0` to run the API without agents (e.g. when running the
  agents separately via ./run_all.sh).

## How a run works (for the demo narration)
1. `POST /api/run` → re-plants the SQLi, creates a Band room, recruits all 4
   agents, posts the CI kickoff mentioning the Hacker.
2. Agents collaborate over Band `@mention` routing; the backend reconstructs the
   full transcript by merging every agent's message view.
3. The Engineer patches the real `target_repo/app.py`; the backend runs the real
   `pytest` suite (🔴 1 failed → 🟢 3 passed).
4. Compliance posts the SOC2/OWASP verdict; the dashboard enables the human gate.
5. `POST /api/approve` → records approval and posts it to the room.
