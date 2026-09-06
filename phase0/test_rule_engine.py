"""
Tests for rule_engine.py -- the generic, config-driven pattern detector.

Run with: pytest phase0/test_rule_engine.py -v
"""

from pathlib import Path
from rule_engine import run_rules

SAMPLES_DIR = Path(__file__).parent / "samples"


def _rule_ids(findings):
    return {f["rule_id"] for f in findings}


def test_detects_legacy_var_in_js():
    findings = run_rules(SAMPLES_DIR / "legacy_jquery.js", "javascript")
    assert "legacy-var" in _rule_ids(findings)
    var_findings = [f for f in findings if f["rule_id"] == "legacy-var"]
    assert len(var_findings) >= 3


def test_detects_jquery_call():
    findings = run_rules(SAMPLES_DIR / "legacy_jquery.js", "javascript")
    assert "jquery-call" in _rule_ids(findings)


def test_detects_prototype_pattern():
    findings = run_rules(SAMPLES_DIR / "legacy_jquery.js", "javascript")
    assert "prototype-pattern" in _rule_ids(findings)


def test_no_false_positive_for_strict_equality():
    # a file with only `===` should NOT trigger the loose-equality rule
    tmp_path = SAMPLES_DIR / "_tmp_strict_eq.js"
    tmp_path.write_text("if (a === b) { console.log('ok'); }")
    try:
        findings = run_rules(tmp_path, "javascript")
        assert "loose-equality" not in _rule_ids(findings)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def test_detects_py2_has_key():
    findings = run_rules(SAMPLES_DIR / "legacy_python2.py", "python")
    assert "py2-has-key" in _rule_ids(findings)


def test_detects_py2_urllib2_import():
    findings = run_rules(SAMPLES_DIR / "legacy_python2.py", "python")
    assert "py2-urllib2" in _rule_ids(findings)


def test_findings_are_sorted_by_line():
    findings = run_rules(SAMPLES_DIR / "legacy_jquery.js", "javascript")
    lines = [f["line"] for f in findings]
    assert lines == sorted(lines)


def test_clean_file_has_no_findings():
    tmp_path = SAMPLES_DIR / "_tmp_clean.py"
    tmp_path.write_text("def add(a, b):\n    return a + b\n")
    try:
        findings = run_rules(tmp_path, "python")
        assert findings == []
    finally:
        if tmp_path.exists():
            tmp_path.unlink()
