"""🕵️  The Hacker — Threat Analyst.  Framework: CrewAI.

Parses the alert, inspects the repo, pinpoints the exploit vector, and hands a
structured threat brief to the Engineer via an @mention in the Band room.
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


# --- tools (CrewAI form: (InputModel, fn)) ---------------------------------

class Empty(BaseModel):
    pass


class ReadInput(BaseModel):
    filename: str = Field(..., description="Source file name, e.g. app.py")


def scan_repo(_: Empty) -> str:
    return T.scan_repo()


def list_repo(_: Empty) -> str:
    return T.list_repo()


def read_source(inp: ReadInput) -> str:
    return T.read_source(inp.filename)


CUSTOM = """You are THE HACKER, an elite white-hat threat analyst in a security
remediation swarm. Your job:
1. Call list_repo and scan_repo to discover the codebase and find the vulnerability.
2. Call read_source on the suspicious file to confirm the exact exploit vector.
3. Post ONE message to the room that @mentions the Engineer with a structured
   threat brief: file & line, vulnerability class (CWE + OWASP), a concrete
   exploit payload, and the required remediation direction.
Be precise and concise. Do NOT write the fix yourself — that is the Engineer's job.
After you hand off, stop."""


async def main():
    load_dotenv()
    agent_id, api_key = load_agent_config("hacker")
    adapter = CrewAIAdapter(
        model=crewai_model(),
        role="White-Hat Threat Analyst",
        goal="Find and precisely characterize the security vulnerability, then hand off to the Engineer.",
        backstory="A veteran penetration tester who lives for finding the one line that breaks everything.",
        custom_section=CUSTOM,
        verbose=True,
        additional_tools=[
            (Empty, list_repo),
            (Empty, scan_repo),
            (ReadInput, read_source),
        ],
    )
    agent = Agent.create(adapter=adapter, agent_id=agent_id, api_key=api_key)
    logging.info("🕵️  Hacker online. Waiting for the room...")
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
