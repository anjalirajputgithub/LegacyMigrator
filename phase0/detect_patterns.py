"""
Phase 0, step 2: first taste of AST-based pattern detection.

This is deliberately tiny -- just enough to prove the concept that Phase 1
will formalize into a real service: walk the tree, look at node TYPES and
STRUCTURE (not text/regex), and flag legacy patterns with their exact
location.

Why not regex? A regex for "var " would also match the word "variable" in a
string or comment. Matching on node.type == "var" only fires on an actual
`var` keyword token recognized by the grammar -- this is the core reason
AST-based tools are more reliable than text search, and it's the argument
you can make in an interview when asked "why not just use regex here?"
"""

from pathlib import Path
from tree_sitter_languages import get_parser

SAMPLES_DIR = Path(__file__).parent / "samples"


def find_all(node, node_type):
    """Yield every descendant node matching a given tree-sitter node type."""
    if node.type == node_type:
        yield node
    for child in node.children:
        yield from find_all(child, node_type)


def detect_js_patterns(path: Path):
    parser = get_parser("javascript")
    source = path.read_bytes()
    tree = parser.parse(source)
    findings = []

    # Pattern 1: `var` declarations -> should become let/const
    for node in find_all(tree.root_node, "var"):
        line = node.start_point[0] + 1
        findings.append((line, "legacy-var", "Use of 'var' -- migrate to let/const"))

    # Pattern 2: jQuery `$(...)` calls -> candidate for React/DOM API migration
    for node in find_all(tree.root_node, "call_expression"):
        callee = node.child_by_field_name("function")
        if callee is not None and source[callee.start_byte:callee.end_byte] == b"$":
            line = node.start_point[0] + 1
            findings.append((line, "jquery-call", "jQuery '$(...)' call -- candidate for React/DOM migration"))

    # Pattern 3: .prototype. assignment -> candidate for ES6 class syntax
    for node in find_all(tree.root_node, "member_expression"):
        prop = node.child_by_field_name("property")
        if prop is not None and source[prop.start_byte:prop.end_byte] == b"prototype":
            line = node.start_point[0] + 1
            findings.append((line, "prototype-pattern", "'.prototype.' assignment -- candidate for ES6 class syntax"))

    return findings


def detect_py2_patterns(path: Path):
    parser = get_parser("python")
    source = path.read_bytes()
    tree = parser.parse(source)
    findings = []

    # Pattern 1: dict.has_key(...) -> removed in Python 3, should be `in`
    for node in find_all(tree.root_node, "call_expression"):
        pass  # python grammar uses "call", not "call_expression" -- see below

    for node in find_all(tree.root_node, "call"):
        fn = node.child_by_field_name("function")
        if fn is not None and fn.type == "attribute":
            attr = fn.child_by_field_name("attribute")
            if attr is not None and source[attr.start_byte:attr.end_byte] == b"has_key":
                line = node.start_point[0] + 1
                findings.append((line, "py2-has-key", "'.has_key()' removed in Python 3 -- migrate to 'in'"))

    # Pattern 2: print as a statement without parens shows up as two
    # sibling expression_statements with no operator between them in some
    # grammars, or as a syntax error in others -- flag any parse error region
    # as a manual-review candidate.
    def find_errors(node):
        if node.type == "ERROR" or node.is_missing:
            yield node
        for c in node.children:
            yield from find_errors(c)

    for node in find_errors(tree.root_node):
        line = node.start_point[0] + 1
        findings.append((line, "parse-error", "Grammar could not cleanly parse this region -- likely Python 2-only syntax"))

    return findings


if __name__ == "__main__":
    print("JS findings (legacy_jquery.js):")
    for line, tag, msg in sorted(detect_js_patterns(SAMPLES_DIR / "legacy_jquery.js")):
        print(f"  line {line:>3}  [{tag}]  {msg}")

    print("\nPython findings (legacy_python2.py):")
    for line, tag, msg in sorted(detect_py2_patterns(SAMPLES_DIR / "legacy_python2.py")):
        print(f"  line {line:>3}  [{tag}]  {msg}")
