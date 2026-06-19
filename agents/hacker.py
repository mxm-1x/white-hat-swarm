"""🕵️  The Hacker — Threat Analyst.  Framework: CrewAI.

Parses the alert, inspects the repo, pinpoints the exploit vector, and hands a
structured threat brief to the Engineer via an @mention in the Band room.

NOTE on tool names: the Band CrewAI adapter derives each tool's name from its
input MODEL class name (lowercased, trailing "Input" stripped). So ScanInput ->
"scan", ListInput -> "list", ReadFileInput -> "readfile". The custom_section
below references those derived names. Each model also has a real field because
Groq rejects no-property tool schemas.
"""

import asyncio
import logging

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from band import Agent, AdapterFeatures
from band.adapters import CrewAIAdapter
from band.config import load_agent_config

import swarm_tools as T
from llm import crewai_model

logging.basicConfig(level=logging.INFO)


class ScanInput(BaseModel):
    target: str = Field("repo", description="Set to 'repo' to scan the target repository.")


class ListInput(BaseModel):
    target: str = Field("repo", description="Set to 'repo' to list repository files.")


class ReadFileInput(BaseModel):
    filename: str = Field(..., description="Source file name, e.g. app.py")


def scan(inp: ScanInput) -> str:
    return T.scan_repo()


def listfiles(inp: ListInput) -> str:
    return T.list_repo()


def readfile(inp: ReadFileInput) -> str:
    return T.read_source(inp.filename)


CUSTOM = """You are THE HACKER, an elite white-hat threat analyst in a security
remediation swarm. Your tools: `list` (list repo files), `scan` (static scan for
vulnerabilities), `readfile` (read a file's source).
Your job when asked to investigate:
1. Call `list`, then `scan` to find the vulnerability.
2. Call `readfile` on the flagged file to confirm the exact exploit vector.
3. Send ONE message via band_send_message with a structured threat brief:
   file & line, vulnerability class (CWE + OWASP), a concrete exploit payload,
   and the required remediation direction.
   Set the `mentions` argument to the JSON array string ["@malharmahanor/engineer"]
   so it routes to the Engineer. (mentions is a STRING containing a JSON array.)
Be precise and concise. Do NOT write the fix yourself — that is the Engineer's job.
After you hand off, stop.
IMPORTANT: Only act on the initial CI security alert. For any later message —
acknowledgements, approvals, verdicts — take NO action and do NOT send a message."""


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
        features=AdapterFeatures(include_tools=["band_send_message"]),
        additional_tools=[
            (ListInput, listfiles),
            (ScanInput, scan),
            (ReadFileInput, readfile),
        ],
    )
    agent = Agent.create(adapter=adapter, agent_id=agent_id, api_key=api_key)
    logging.info("🕵️  Hacker online. Waiting for the room...")
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
