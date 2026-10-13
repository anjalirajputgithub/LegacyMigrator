"""
The actual agent: propose a migration -> critique it against the
original -> either loop back for a revision, or finalize.

This is the piece that makes this an AGENT rather than a single prompt
call. A plain "ask the LLM to migrate this code" is one API call with no
self-checking. Here, the LLM's own output gets reviewed by a second LLM
call before anything is returned -- closer to how a human would draft,
then re-read their own work before submitting it.
"""

import re
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field
from typing import Literal

from app.agent.state import MigrationState
from app.agent.llm import get_llm
from app.agent.prompt import (
    PROPOSE_SYSTEM_PROMPT, PROPOSE_USER_TEMPLATE,
    CRITIQUE_SYSTEM_PROMPT, CRITIQUE_USER_TEMPLATE,
    format_findings,
)

MAX_REVISIONS = 2  # safety limit -- never loop forever, even if the LLM keeps saying "revise"


def _extract_code_block(text: str) -> str:
    """Pulls the code out of a ```lang ... ``` fenced block. Falls back to
    the raw text if the model didn't fence it (defensive -- LLMs don't
    always follow formatting instructions perfectly)."""
    match = re.search(r"```(?:\w+)?\n(.*?)```", text, re.DOTALL)
    return match.group(1).strip() if match else text.strip()


class CritiqueResult(BaseModel):
    verdict: Literal["approve", "revise"] = Field(description="approve if the migration is correct and complete, revise otherwise")
    critique: str = Field(description="Specific, actionable feedback -- what's wrong and what to fix")


def propose_node(state: MigrationState) -> dict:
    llm = get_llm()
    findings_list = format_findings(state["findings"])

    messages = [
        SystemMessage(content=PROPOSE_SYSTEM_PROMPT),
        HumanMessage(content=PROPOSE_USER_TEMPLATE.format(
            language=state["language"],
            source_code=state["source_code"],
            findings_list=findings_list,
        )),
    ]

    # If this is a revision (not the first attempt), include the prior
    # critique so the model knows what to fix instead of guessing again.
    if state.get("critique"):
        messages.append(HumanMessage(
            content=f"Your previous attempt was rejected for this reason:\n{state['critique']}\n\nTry again."
        ))

    response = llm.invoke(messages)
    proposed_code = _extract_code_block(response.content)

    return {"proposed_code": proposed_code}


def critique_node(state: MigrationState) -> dict:
    llm = get_llm().with_structured_output(CritiqueResult)
    findings_list = format_findings(state["findings"])

    messages = [
        SystemMessage(content=CRITIQUE_SYSTEM_PROMPT),
        HumanMessage(content=CRITIQUE_USER_TEMPLATE.format(
            language=state["language"],
            source_code=state["source_code"],
            findings_list=findings_list,
            proposed_code=state["proposed_code"],
        )),
    ]

    result: CritiqueResult = llm.invoke(messages)

    return {
        "critique": result.critique,
        "verdict": result.verdict,
        "revision_count": state.get("revision_count", 0) + 1,
    }


def finalize_node(state: MigrationState) -> dict:
    return {
        "final_code": state["proposed_code"],
        "explanation": state["critique"] or "Migration approved with no issues on first attempt.",
    }


def route_after_critique(state: MigrationState) -> str:
    """Decides: loop back for another attempt, or finalize.
    This is the actual 'agentic' decision point in the graph."""
    if state["verdict"] == "approve":
        return "finalize"
    if state["revision_count"] >= MAX_REVISIONS:
        # Ran out of attempts -- finalize with whatever we have rather
        # than looping forever. The explanation will make clear it wasn't
        # fully approved.
        return "finalize"
    return "propose"


def build_graph():
    graph = StateGraph(MigrationState)

    graph.add_node("propose", propose_node)
    graph.add_node("critique", critique_node)
    graph.add_node("finalize", finalize_node)

    graph.set_entry_point("propose")
    graph.add_edge("propose", "critique")
    graph.add_conditional_edges("critique", route_after_critique, {
        "propose": "propose",
        "finalize": "finalize",
    })
    graph.add_edge("finalize", END)

    return graph.compile()


# Compiled once at import time, reused across requests.
migration_graph = build_graph()


def run_migration(source_code: str, language: str, findings: list[dict]) -> dict:
    """The one function the API layer calls."""
    initial_state: MigrationState = {
        "source_code": source_code,
        "language": language,
        "findings": findings,
        "proposed_code": "",
        "critique": "",
        "verdict": "",
        "revision_count": 0,
        "final_code": "",
        "explanation": "",
    }
    result = migration_graph.invoke(initial_state)
    return {
        "final_code": result["final_code"],
        "explanation": result["explanation"],
        "revisions": result["revision_count"],
    }