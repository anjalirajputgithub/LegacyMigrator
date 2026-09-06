# Legacy Migrator (AI Software Engineer for Legacy Code Migration)

An AI-assisted tool to analyze legacy codebases (jQuery/ES5 JavaScript and
Python 2) and detect outdated patterns as a first step toward automated
migration.

## Status: Phase 0 — exploring tree-sitter

Right now this repo just proves the core idea works: parse source code into
a syntax tree using tree-sitter, then walk that tree to detect legacy
patterns by structure, not text matching.

## What's here

- `phase0/parse_ast.py` — parses a file and pretty-prints its syntax tree
- `pphase0/rule_engine.py` — walks the tree and flags legacy patterns
  (e.g. `var` usage, jQuery calls, `.has_key()`)
- `phase0/samples/` — example legacy JS and Python 2 files used for testing

## Run it

```bash
cd phase0
pip install -r requirements.txt
python3 parse_ast.py
python phase0/rule_engine.py
pytest phase0/test_rule_engine.py -v
```

## What's next

More phases planned (a real API, LLM-based migration suggestions, a web
dashboard) — not built yet. This README will grow as the project does.
