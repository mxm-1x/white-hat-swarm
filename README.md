# 🛡️ White-Hat — Autonomous Remediation Swarm

**Track 3 — Regulated & High-Stakes Workflows · built on [Band.ai](https://band.ai)**

### 🔗 Live demo dashboard: https://mxm-1x.github.io/white-hat-swarm/

A static "Remediation Command Center" that replays the swarm's run — the four agents, the
Band hand-off chain, the 🔴→🟢 test flip, the SOC2/OWASP verdict, and the SHA-256-sealed
manifest with a working human-approval gate.

```
         [ CI / CD pipeline  or  Human ]
                       |
                       |   "@Hacker  possible SQL injection in acme-billing"
                       v
  .--------------------------------  BAND ROOM  ----------------------------.
  |  .----------.     .----------.     .----------.     .------------.      |
  |  |  HACKER  | --> | ENGINEER | --> | QA TESTER| --> | COMPLIANCE |      |
  |  |  CrewAI  |     | LangGraph|     | LangGraph|     |   CrewAI   |      |
  |  |~~~~~~~~~~|     |~~~~~~~~~~|     |~~~~~~~~~~|     |~~~~~~~~~~~~|      |
  |  | find the |     | write  & |     | run real |     |  SOC2 /    |      |
  |  | exploit  |     | apply    |     | pytest   |     |  OWASP     |      |
  |  | CWE-89   |     | patch    |     | 1F -> 3P |     |  verdict   |      |
  |  '----------'     '----------'     '----------'     '------------'      |
  |       ^                                 |                               |
  |       '-------------- fail loop --------'                               |
  '------------------------------------+------------------------------------'
                                       |
                  verdict  +  [ SHA-256 sealed audit manifest ]
                                       v
                          .----------------------------.
                          |    HUMAN  APPROVAL  GATE    |
                          |     [  Approve & Deploy  ]  |
                          '----------------------------'

      detect -> patch -> verify -> comply -> human-approve
   4 agents | 2 frameworks (CrewAI + LangGraph) | no custom infra
```

Four AI agents — built in **two different frameworks** — collaborate inside a
single Band room to take a security vulnerability from **detection → verified
patch → compliance sign-off**, then hand a **tamper-evident audit manifest** to a
**human approver** for the final high-stakes deployment decision.

This is not alerting. The swarm *fixes* the bug and *proves* the fix, with a
human gate where it legally matters.

---

## The swarm

| Agent | Framework | Does | Band hand-off |
|-------|-----------|------|---------------|
| 🕵️ **Hacker** | **CrewAI** | scans repo, pinpoints exploit (CWE+OWASP) | `@Engineer` threat brief |
| 🔧 **Engineer** | **LangGraph** | writes & applies a root-cause patch | `@QA` patched file |
| 🧪 **QA Tester** | **LangGraph** | runs the real `pytest` suite (red→green) | `@Compliance` pass / `@Engineer` fail-loop |
| 📋 **Compliance** | **CrewAI** | checks patch vs SOC2/OWASP policy | `@Human` verdict |

Cross-framework collaboration is real: CrewAI and LangGraph agents are separate
processes that only share the **Band room** — Band's `@mention` routing is the
entire integration layer. No custom message bus, no shared memory.

**The demo target** (`target_repo/app.py`) ships with a planted **SQL injection
(CWE-89)**. `test_app.py` contains a boundary test that *fails* on the vulnerable
code and *passes* once the query is parameterized — so judges watch the suite go
🔴 → 🟢 live.

---

## One-time setup (~10 min)

### 1. Create 4 External Agents in Band
Dashboard → **Agents → New → External Agent**. Make four: `Hacker`, `Engineer`,
`QA Tester`, `Compliance`. For each, copy the **Agent UUID** and **API key** into
`agent_config.yaml` under the matching key (`hacker`, `engineer`, `qa_tester`,
`compliance`).

### 2. Get an OpenRouter key
https://openrouter.ai/keys → paste into `.env` as `OPENROUTER_API_KEY`.
(`MODEL` defaults to a free, tool-calling-capable model.)

### 3. Install (already done if you ran the build)
```bash
uv sync
```

---

## Run the demo

```bash
# 1. make sure the vulnerability is planted
./reset_demo.sh            # shows the suite FAILING (1 failed)

# 2. bring the swarm online (4 processes, logs in logs/)
./run_all.sh
```

### 3. Open the room in Band
- Create a chat room, add all four agents **and yourself** (the human approver).
- Post the kickoff message, mentioning the Hacker:

> `@Hacker` Security alert from CI: the `acme-billing` service may have an
> injection flaw in the customer lookup path. Investigate `target_repo`, and
> coordinate a verified fix with the team.

Watch the hand-off chain unfold in the room: Hacker → Engineer → QA → Compliance →
you. The Engineer's patch is written to `target_repo/app.py` and QA's pytest run
flips the suite to green — all visible in Band's event stream.

### 4. Seal the audit & approve
```bash
uv run python audit/seal_audit.py        # pulls the transcript, writes a hashed manifest
```
Produces `audit/audit_seal_<chat>.json` — the full Band transcript + a SHA-256
integrity digest, with `human_approval: PENDING`. You, the human, make the call.

To run it again: `./reset_demo.sh` and post a fresh kickoff.

---

## Architecture (what we deliberately did NOT build)

Band's platform **is** the collaboration bus, the real-time dashboard, and the
human approval gate — so there is **no Node/Express, no Postgres, no Next.js**.
The entire system is 4 small Python agents + 1 audit script. That's the point:
Band collapses the infra you'd otherwise hand-roll for multi-agent governance.

```
CI/manual alert ──@mention──▶ Band Room ◀── human approver
                                  │
   Hacker(CrewAI) ─▶ Engineer(LangGraph) ─▶ QA(LangGraph) ─▶ Compliance(CrewAI)
                                  │                  └──(fail)──▲ loop back
                                  ▼
                      audit/seal_audit.py ──▶ SHA-256-sealed manifest ──▶ human gate
```

## Troubleshooting
- **Agent connects but never talks / no tool calls** → the free model isn't
  tool-calling well. Swap `MODEL` in `.env` (try `qwen/qwen-2.5-72b-instruct:free`
  or `deepseek/deepseek-chat-v3-0324:free`) and restart `./run_all.sh`.
- **`KeyError` in agent_config** → the YAML key must match `load_agent_config()`
  in the agent file (`hacker`/`engineer`/`qa_tester`/`compliance`).
- **Audit seal shows few messages** → an agent only sees messages it sent or was
  @mentioned in; seal with `--agent compliance` (default), who's in the loop last.
- **Reset** → `./reset_demo.sh` re-plants the vuln from `shared/app_vulnerable.py`.

## Files
```
agents/        hacker.py engineer.py qa_tester.py compliance.py  +  swarm_tools.py llm.py
target_repo/   app.py (planted SQLi)  test_app.py (red→green boundary test)
shared/        security_policy.md (SOC2/OWASP RAG source)  app_vulnerable.py (reset source)
audit/         seal_audit.py → audit_seal_<chat>.json
```
