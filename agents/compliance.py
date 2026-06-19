"""📋  The Compliance Auditor — Risk Assessor.  Framework: CrewAI.

Checks the patch against internal SOC2 / OWASP policy (RAG-lite over
security_policy.md), then posts a final compliance verdict that @mentions the
human approver. The cryptographic seal of the full Band transcript is produced
by audit/seal_audit.py (run against the room afterward).
"""

import asyncio
import logging

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from band import Agent
from band.adapters import CrewAIAdapter
from band.config import load_agent_config

import swarm_tools as T
from llm import crewai_model

logging.basicConfig(level=logging.INFO)


class Empty(BaseModel):
    pass


class ReadInput(BaseModel):
    filename: str = Field(..., description="Source file name, e.g. app.py")


def read_policy(_: Empty) -> str:
    return T.read_policy()


def read_source(inp: ReadInput) -> str:
    return T.read_source(inp.filename)


CUSTOM = """You are THE COMPLIANCE AUDITOR, the high-stakes policy gatekeeper in a
remediation swarm. When the QA Tester @mentions you that tests pass:
1. Call read_policy to load the SOC2 / OWASP acceptance criteria.
2. Call read_source on the patched file to confirm the fix matches policy
   (parameterized query, no new secrets / network calls / PII handling).
3. Post ONE final message that @mentions the human approver containing a
   compliance verdict: map the fix to the specific controls satisfied
   (e.g. OWASP A03, SOC2 CC7.1/CC7.2), list the acceptance criteria and whether
   each is met, and a clear PASS/FAIL recommendation for production deployment.
You enforce policy; you never approve deployment yourself — that is the human's call."""


async def main():
    load_dotenv()
    agent_id, api_key = load_agent_config("compliance")
    adapter = CrewAIAdapter(
        model=crewai_model(),
        role="Security Compliance Auditor",
        goal="Verify the patch satisfies SOC2/OWASP policy and produce an auditable verdict for the human approver.",
        backstory="A meticulous GRC auditor who has shepherded dozens of SOC2 audits and trusts only evidence.",
        custom_section=CUSTOM,
        verbose=True,
        additional_tools=[
            (Empty, read_policy),
            (ReadInput, read_source),
        ],
    )
    agent = Agent.create(adapter=adapter, agent_id=agent_id, api_key=api_key)
    logging.info("📋  Compliance Auditor online. Waiting for the room...")
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
