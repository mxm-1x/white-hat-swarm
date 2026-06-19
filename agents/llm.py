"""LLM wiring — provider-agnostic via OpenAI-compatible endpoints.

Switch providers with one env var (LLM_PROVIDER) in .env. Default is Groq:
free, fast, generous limits, and reliable tool-calling on llama-3.3-70b —
which matters because Band agents MUST call the band_send_message tool.

LangGraph uses LangChain's ChatOpenAI (base_url + api_key).
CrewAI uses litellm, which selects the provider from the model prefix
(e.g. "groq/...") and reads the provider's key from the environment.
"""

import os

from dotenv import load_dotenv

# Load .env at import time, BEFORE reading env vars below. Agents import this
# module at module-load (before their own load_dotenv() in main()), so without
# this the MODEL/LLM_PROVIDER below would read stale defaults.
load_dotenv()

PROVIDERS = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "key_env": "GROQ_API_KEY",
        "litellm_prefix": "groq/",
        "default_model": "llama-3.3-70b-versatile",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "key_env": "OPENROUTER_API_KEY",
        "litellm_prefix": "openrouter/",
        "default_model": "meta-llama/llama-3.3-70b-instruct:free",
    },
    "google": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "key_env": "GEMINI_API_KEY",
        "litellm_prefix": "gemini/",
        "default_model": "gemini-2.0-flash",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "key_env": "OPENAI_API_KEY",
        "litellm_prefix": "openai/",
        "default_model": "gpt-4o-mini",
    },
}

PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()
if PROVIDER not in PROVIDERS:
    raise ValueError(f"Unknown LLM_PROVIDER={PROVIDER!r}. Options: {list(PROVIDERS)}")
_CFG = PROVIDERS[PROVIDER]
MODEL = os.getenv("MODEL", _CFG["default_model"])


def langgraph_llm():
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=MODEL,
        base_url=_CFG["base_url"],
        api_key=os.environ[_CFG["key_env"]],
        temperature=0,
    )


def crewai_model() -> str:
    # litellm resolves provider + key from this prefix and the env var.
    return f"{_CFG['litellm_prefix']}{MODEL}"
