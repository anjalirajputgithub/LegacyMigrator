"""
These tests mock the LLM entirely -- they prove the GRAPH'S WIRING is
correct (does it loop when told to revise? does it stop looping? does it
finalize correctly?) without spending real API calls or needing a key.
A separate, real-API smoke test should be run once ANTHROPIC_API_KEY is
set, to confirm actual model behavior -- these tests can't catch prompt
quality issues, only control-flow bugs.
"""

from unittest.mock import patch, MagicMock
from app.agent.graph import build_graph, MAX_REVISIONS


def _fake_propose_response(code: str):
    msg = MagicMock()
    msg.content = f"```python\n{code}\n```"
    return msg


def test_approves_on_first_attempt():
    graph = build_graph()

    mock_llm = MagicMock()
    mock_llm.invoke.return_value = _fake_propose_response("fixed_code_v1")
    mock_structured = MagicMock()
    mock_structured.invoke.return_value = MagicMock(verdict="approve", critique="Looks good.")
    mock_llm.with_structured_output.return_value = mock_structured

    with patch("app.agent.graph.get_llm", return_value=mock_llm):
        result = graph.invoke({
            "source_code": "var x = 1;", "language": "javascript",
            "findings": [{"rule_id": "legacy-var", "message": "use let", "line": 1}],
            "proposed_code": "", "critique": "", "verdict": "",
            "revision_count": 0, "final_code": "", "explanation": "",
        })

    assert result["final_code"] == "fixed_code_v1"
    assert result["revision_count"] == 1  # critique ran exactly once


def test_loops_once_then_approves():
    graph = build_graph()

    mock_llm = MagicMock()
    mock_llm.invoke.return_value = _fake_propose_response("attempt")

    mock_structured = MagicMock()
    # First critique call says revise, second says approve
    mock_structured.invoke.side_effect = [
        MagicMock(verdict="revise", critique="Missing a fix."),
        MagicMock(verdict="approve", critique="Now it's correct."),
    ]
    mock_llm.with_structured_output.return_value = mock_structured

    with patch("app.agent.graph.get_llm", return_value=mock_llm):
        result = graph.invoke({
            "source_code": "var x = 1;", "language": "javascript",
            "findings": [{"rule_id": "legacy-var", "message": "use let", "line": 1}],
            "proposed_code": "", "critique": "", "verdict": "",
            "revision_count": 0, "final_code": "", "explanation": "",
        })

    assert result["revision_count"] == 2  # critique ran twice
    assert result["explanation"] == "Now it's correct."


def test_stops_after_max_revisions_even_if_never_approved():
    graph = build_graph()

    mock_llm = MagicMock()
    mock_llm.invoke.return_value = _fake_propose_response("attempt")

    mock_structured = MagicMock()
    # Always says revise -- graph must not loop forever
    mock_structured.invoke.return_value = MagicMock(verdict="revise", critique="Still wrong.")
    mock_llm.with_structured_output.return_value = mock_structured

    with patch("app.agent.graph.get_llm", return_value=mock_llm):
        result = graph.invoke({
            "source_code": "var x = 1;", "language": "javascript",
            "findings": [{"rule_id": "legacy-var", "message": "use let", "line": 1}],
            "proposed_code": "", "critique": "", "verdict": "",
            "revision_count": 0, "final_code": "", "explanation": "",
        })

    # Should stop at MAX_REVISIONS, not loop indefinitely
    assert result["revision_count"] == MAX_REVISIONS
    assert result["final_code"] == "attempt"