"""
One place that knows how to talk to the LLM. If you ever swap providers
or models, this is the only file that changes -- graph.py never
constructs an LLM client directly.
"""

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

# Configurable via env var so you're not stuck with one hardcoded model.
DEFAULT_MODEL = os.environ.get("MIGRATION_AGENT_MODEL", "qwen/qwen3.8-27b")


def get_llm(temperature: float = 0.0):
    """Returns a chat model client. temperature=0 by default -- for code
    migration you want deterministic, consistent output, not creativity.

    Requires GROQ_API_KEY to be set in .env or as an environment variable.
    """
    return ChatGroq(
        model=DEFAULT_MODEL,
        temperature=temperature,
        api_key=os.environ.get("GROQ_API_KEY"),
    )