"""LLM wiring for OpenRouter (free models).

LangGraph uses LangChain's ChatOpenAI pointed at OpenRouter's OpenAI-compatible
endpoint. CrewAI uses litellm, which speaks OpenRouter via the ``openrouter/``
model prefix and reads ``OPENROUTER_API_KEY`` from the environment.

Override the model per run with the MODEL env var. The default is a free,
tool-calling-capable model — tool calling is REQUIRED because Band agents must
invoke the ``band_send_message`` platform tool to talk in the room.
"""

import os

# Free OpenRouter models that reliably support tool/function calling.
# If you hit rate limits or "no tools" errors, swap to another from this list.
DEFAULT_MODEL = os.getenv("MODEL", "meta-llama/llama-3.3-70b-instruct:free")


def langgraph_llm():
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=DEFAULT_MODEL,
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
        temperature=0,
    )


def crewai_model() -> str:
    # litellm prefix; OPENROUTER_API_KEY is read from env automatically.
    return f"openrouter/{DEFAULT_MODEL}"
