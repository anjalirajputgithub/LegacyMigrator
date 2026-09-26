"""
Tests the actual HTTP layer, not just the analyzer engine directly -- this
catches bugs in request validation, status codes, and response shape that
unit-testing analyze_code() alone wouldn't catch.
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_analyze_detects_legacy_var():
    resp = client.post("/analyze", json={
        "code": "var x = 1;",
        "language": "javascript",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["finding_count"] == 1
    assert data["findings"][0]["rule_id"] == "legacy-var"


def test_analyze_detects_py2_has_key():
    resp = client.post("/analyze", json={
        "code": "if d.has_key('x'):\n    pass",
        "language": "python",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert any(f["rule_id"] == "py2-has-key" for f in data["findings"])


def test_analyze_clean_code_returns_no_findings():
    resp = client.post("/analyze", json={
        "code": "const x = 1;",
        "language": "javascript",
    })
    assert resp.status_code == 200
    assert resp.json()["finding_count"] == 0


def test_analyze_rejects_missing_code():
    resp = client.post("/analyze", json={"language": "javascript"})
    assert resp.status_code == 422  # FastAPI's automatic validation error


def test_analyze_rejects_unsupported_language():
    resp = client.post("/analyze", json={"code": "x = 1", "language": "ruby"})
    assert resp.status_code == 422  # Literal type rejects it before it reaches our code
