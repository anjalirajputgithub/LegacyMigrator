"""
Generic, config-driven pattern detector with robust validation and query caching.

Reads declarative pattern rules from rules.yaml, pre-compiles Tree-sitter
queries once for efficiency, validates rule schemas, and deduplicates matches.
"""

from pathlib import Path
from typing import List, Dict, Any
import logging
import yaml

# Standard modern tree-sitter imports (tree-sitter >= 0.22)
from tree_sitter import Language, Parser, Query
import tree_sitter_python as tspython
import tree_sitter_javascript as tsjavascript

LANGUAGES = {
    "python": Language(tspython.language()),
    "javascript": Language(tsjavascript.language()),
}


def get_lang_and_parser(language: str):
    lang = LANGUAGES.get(language)
    if not lang:
        raise ValueError(f"Unsupported language: '{language}'")
    return lang, Parser(lang)


def execute_query(lang, query_obj, root_node):
    """Executes a compiled query against a root node across different tree-sitter version APIs."""
    try:
        from tree_sitter import QueryCursor
        cursor = QueryCursor(query_obj)
        captures = cursor.captures(root_node)
        if isinstance(captures, dict):
            results = []
            for cap_name, nodes in captures.items():
                for node in nodes:
                    results.append((node, cap_name))
            return results
        elif isinstance(captures, list):
            return captures
    except (ImportError, AttributeError):
        pass

    # Fallback for direct query.captures API
    if hasattr(query_obj, "captures"):
        captures = query_obj.captures(root_node)
        if isinstance(captures, dict):
            results = []
            for cap_name, nodes in captures.items():
                for node in nodes:
                    results.append((node, cap_name))
            return results
        return captures

    return []


RULES_FILE = Path(__file__).parent / "rules.yaml"
SAMPLES_DIR = Path(__file__).parent / "samples"
logger = logging.getLogger("ASTRuleEngine")


class ASTRuleEngine:
    """Production-ready AST Rule Engine with schema validation & query caching."""

    def __init__(self, rules_path: Path = RULES_FILE):
        self.rules_path = rules_path
        self._compiled_queries: Dict[str, List[Dict[str, Any]]] = {}
        self.load_rules()

    def load_rules(self):
        """Loads and pre-compiles queries once at startup with schema validation."""
        if not self.rules_path.exists():
            raise FileNotFoundError(f"Rules file missing: {self.rules_path}")

        try:
            with open(self.rules_path, "r", encoding="utf-8") as f:
                all_rules = yaml.safe_load(f) or {}
        except Exception as e:
            raise ValueError(f"Invalid YAML syntax in {self.rules_path}: {e}")

        required_keys = {"id", "message", "query"}

        for lang_name, rules in all_rules.items():
            if not isinstance(rules, list):
                continue

            try:
                lang, _ = get_lang_and_parser(lang_name)
            except Exception as e:
                logger.warning(f"Skipping language '{lang_name}': {e}")
                continue

            compiled_rules = []
            for idx, rule in enumerate(rules):
                # 1. Schema Validation
                missing = required_keys - set(rule.keys())
                if missing:
                    logger.error(f"Rule #{idx+1} in '{lang_name}' missing required keys {missing}. Skipping.")
                    continue

                # 2. Query Syntax Pre-Compilation
                try:
                    query_obj = Query(lang, rule["query"])
                    compiled_rules.append({
                        "id": rule["id"],
                        "severity": rule.get("severity", "info"),
                        "message": rule["message"],
                        "query_obj": query_obj,
                    })
                except Exception as err:
                    logger.error(f"Invalid Tree-sitter query in rule '{rule.get('id', idx)}': {err}")

            self._compiled_queries[lang_name] = compiled_rules

    def run_rules(self, path: Path, language: str) -> List[Dict[str, Any]]:
        """Analyzes a source file against pre-compiled rules."""
        if not path.exists():
            logger.error(f"File not found: {path}")
            return []

        rules = self._compiled_queries.get(language, [])
        if not rules:
            return []

        try:
            lang, parser = get_lang_and_parser(language)
            source = path.read_bytes()
            tree = parser.parse(source)
        except Exception as e:
            logger.error(f"Failed to parse source file {path}: {e}")
            return []

        findings = []
        seen = set()

        for rule in rules:
            try:
                captures = execute_query(lang, rule["query_obj"], tree.root_node)
            except Exception as capture_err:
                logger.error(f"Error executing query for rule '{rule['id']}': {capture_err}")
                continue

            for node, capture_name in captures:
                if capture_name != "match":
                    continue

                # 3. Deduplication Check (line, rule_id, start_byte, end_byte)
                dedup_key = (node.start_point[0] + 1, rule["id"], node.start_byte, node.end_byte)
                if dedup_key in seen:
                    continue
                seen.add(dedup_key)

                findings.append({
                    "line": node.start_point[0] + 1,
                    "rule_id": rule["id"],
                    "severity": rule["severity"],
                    "message": rule["message"],
                    "snippet": source[node.start_byte:node.end_byte].decode(errors="replace")[:60],
                })

        return sorted(findings, key=lambda f: f["line"])


def run_rules(path: Path, language: str) -> List[Dict[str, Any]]:
    """Helper function maintaining backwards compatibility with existing calls."""
    engine = ASTRuleEngine()
    return engine.run_rules(path, language)


if __name__ == "__main__":
    engine = ASTRuleEngine()

    js_file = SAMPLES_DIR / "legacy_jquery.js"
    if js_file.exists():
        print("JavaScript findings:")
        for f in engine.run_rules(js_file, "javascript"):
            print(f"  line {f['line']:>3}  [{f['severity']:>7}] {f['rule_id']:<20} {f['message']}")

    py_file = SAMPLES_DIR / "legacy_python2.py"
    if py_file.exists():
        print("\nPython findings:")
        for f in engine.run_rules(py_file, "python"):
            print(f"  line {f['line']:>3}  [{f['severity']:>7}] {f['rule_id']:<20} {f['message']}")