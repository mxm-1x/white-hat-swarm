"""🔧  The Engineer — Patch Developer.  Framework: LangGraph.

Receives the threat brief, reads the source, writes a parameterized fix, applies
it, and hands the patched file to the QA Tester via an @mention. If QA reports a
failure, the Engineer is mentioned again and iterates.
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
def read_source(filename: str) -> str:
    """Read a source file from the target repo. Args: filename e.g. 'app.py'."""
    return T.read_source(filename)


@tool
def apply_patch(filename: str, new_content: str) -> str:
    """Overwrite a source file with the fixed version.

    Args:
        filename: file to patch, e.g. 'app.py'
        new_content: the COMPLETE new contents of the file
    """
    return T.apply_patch(filename, new_content)


CUSTOM = """You are THE ENGINEER, a secure-coding specialist in a remediation swarm.
When the Hacker @mentions you with a threat brief:
1. Call read_source on the affected file.
2. Fix the ROOT CAUSE (e.g. replace string-built SQL with a parameterized query
   using '?' placeholders and a params tuple). Do not merely filter input.
3. Call apply_patch with the COMPLETE corrected file contents.
4. Post ONE message via band_send_message summarizing the change and asking them
   to run the test suite. Set mentions to ["@malharmahanor/qa-tester"] so it
   routes to the QA Tester.
If the QA Tester later @mentions you with failing tests, read the logs, fix, and
re-apply, then message QA again with mentions ["@malharmahanor/qa-tester"].
Keep the public message short; put code in the patch."""


async def main():
    load_dotenv()
    agent_id, api_key = load_agent_config("engineer")
    adapter = LangGraphAdapter(
        llm=langgraph_llm(),
        checkpointer=InMemorySaver(),
        additional_tools=[read_source, apply_patch],
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
    logging.info("🔧  Engineer online. Waiting for the room...")
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
