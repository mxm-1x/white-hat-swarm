"""🧪  The QA Tester — Regression Specialist.  Framework: LangGraph.

Runs the real pytest suite against the patched repo. If green, @mentions the
Compliance Auditor to seal the audit. If red, @mentions the Engineer with logs.
"""

import asyncio
import logging
import os

from dotenv import load_dotenv
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver

from band import Agent, AdapterFeatures
from band.adapters import LangGraphAdapter
from band.config import load_agent_config

import swarm_tools as T
from llm import langgraph_llm

logging.basicConfig(level=logging.INFO)


@tool
def run_tests(scope: str = "all") -> str:
    """Run the target repo's pytest suite and return a pass/fail summary.

    Args:
        scope: optional, ignored; pass "all" to run the full suite.
    """
    return T.run_tests()


@tool
def read_source(filename: str) -> str:
    """Read a source file from the target repo. Args: filename e.g. 'app.py'."""
    return T.read_source(filename)


CUSTOM = """You are THE QA TESTER, a deterministic regression specialist in a
remediation swarm. When the Engineer @mentions you that a patch is ready:
1. Call run_tests to execute the full suite (functional + the SQL-injection
   boundary test).
2. If ALL TESTS PASS: send ONE message with the test summary and a request to
   seal the audit, with mentions ["@malharmahanor/compliance-agent"].
3. If TESTS FAILED: send ONE message with the failing output so they can fix it,
   with mentions ["@malharmahanor/engineer"]. Do not attempt to fix code yourself.
Report results factually — never claim a pass you did not see in the tool output."""


async def main():
    load_dotenv()
    agent_id, api_key = load_agent_config("qa_tester")
    adapter = LangGraphAdapter(
        llm=langgraph_llm(),
        checkpointer=InMemorySaver(),
        additional_tools=[run_tests, read_source],
        custom_section=CUSTOM,
        features=AdapterFeatures(include_tools=["band_send_message"]),
    )
    agent = Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
        ws_url=os.getenv("BAND_WS_URL", "wss://app.band.ai/api/v1/socket/websocket"),
        rest_url=os.getenv("BAND_REST_URL", "https://app.band.ai"),
    )
    logging.info("🧪  QA Tester online. Waiting for the room...")
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
