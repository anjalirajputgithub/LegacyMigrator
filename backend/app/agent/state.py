"""
The graph's shared state. Every node reads from this and returns updates
to it -- LangGraph merges those updates back in automatically. Think of
this as the one "form" that gets passed from station to station, with
each station filling in a new field.
"""

from typing import TypedDict, Literal


class MigrationState(TypedDict):
    # Set once at the start, never changed by nodes:
    source_code: str
    language: str
    findings: list[dict]          # from Phase 1's analyzer -- the "what's wrong" list

    # Filled in as the graph runs:
    proposed_code: str            # the LLM's migration attempt
    critique: str                 # the LLM's own review of its attempt
    verdict: Literal["approve", "revise", ""]  # decides whether to loop back
    revision_count: int           # safety limit so it can't loop forever
    final_code: str               # what actually gets returned to the caller
    explanation: str              # human-readable summary of what changed and why