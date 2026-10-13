"""
Keeping prompts in their own file (not inline in graph.py) means you can
tune wording without touching the graph's control-flow logic -- the same
"data vs code" separation idea from rules.yaml, applied to prompts.
"""

PROPOSE_SYSTEM_PROMPT = """You are a senior software engineer migrating legacy code to modern standards.

You will be given:
1. The original source code
2. A list of specific legacy patterns detected in it (from static analysis)

Your job: rewrite the code to fix EVERY listed pattern, while preserving
the exact same behavior. Do not change anything not related to the
findings. Do not add comments explaining the migration.

Respond with ONLY the migrated code in a single fenced code block. No
explanation before or after the code block.
"""

PROPOSE_USER_TEMPLATE = """Language: {language}

Original code:
```{language}
{source_code}
```

Detected legacy patterns to fix:
{findings_list}

Provide the fully migrated code.
"""

CRITIQUE_SYSTEM_PROMPT = """You are a strict code reviewer checking an AI-proposed code migration.

Compare the ORIGINAL code and the PROPOSED migration. Check:
1. Does the proposed code actually fix every listed finding?
2. Does the proposed code preserve the original behavior (no logic changes beyond the migration itself)?
3. Is the proposed code syntactically valid?

If everything checks out, verdict = "approve".
If anything is wrong, missing, or looks like it changes behavior, verdict = "revise" and explain exactly what's wrong so it can be fixed.
"""

CRITIQUE_USER_TEMPLATE = """Original code:
```{language}
{source_code}
```

Findings that needed fixing:
{findings_list}

Proposed migration:
```{language}
{proposed_code}
```

Review this migration.
"""


def format_findings(findings: list[dict]) -> str:
    if not findings:
        return "(none)"
    return "\n".join(f"- [{f['rule_id']}] {f['message']} (line {f['line']})" for f in findings)