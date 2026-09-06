"""
Phase 0: Learn tree-sitter.

Parses a legacy JS (jQuery) file and a legacy Python 2 file, then pretty-prints
their syntax trees. The goal here isn't to detect anything yet -- it's to get
comfortable reading what tree-sitter actually gives you, since every later
phase (pattern detection, RAG chunking, migration) is built on top of this.
"""

from pathlib import Path
from tree_sitter import Language, Parser
import tree_sitter_javascript  # type: ignore
import tree_sitter_python      # type: ignore


def get_parser(language_name: str) -> Parser:
    if language_name == "javascript":
        lang_ptr = tree_sitter_javascript.language()
    elif language_name == "python":
        lang_ptr = tree_sitter_python.language()
    else:
        raise ValueError(f"Unsupported language: {language_name}")
    
    return Parser(Language(lang_ptr))

SAMPLES_DIR = Path(__file__).parent / "samples"


def pretty_print(node, source: bytes, depth: int = 0, max_depth: int = 6):
    """Recursively print a tree-sitter node, indented by depth.

    Leaf tokens (no children) show their actual source text so you can see
    exactly what matched -- the sexp() output alone hides this.
    """
    indent = "  " * depth
    if depth > max_depth:
        print(f"{indent}... (truncated, use max_depth to see more)")
        return

    if node.child_count == 0:
        text = source[node.start_byte:node.end_byte].decode(errors="replace")
        text = text if len(text) <= 40 else text[:37] + "..."
        print(f"{indent}{node.type}  \"{text}\"  [{node.start_point[0]+1}:{node.start_point[1]}]")
    else:
        print(f"{indent}{node.type}  [{node.start_point[0]+1}:{node.start_point[1]}]")
        for child in node.children:
            pretty_print(child, source, depth + 1, max_depth)


def parse_file(path: Path, language: str, max_depth: int = 6):
    parser = get_parser(language)
    source = path.read_bytes()
    tree = parser.parse(source)

    print("=" * 70)
    print(f"FILE: {path.name}   (grammar: {language})")
    print(f"Parse contains errors: {tree.root_node.has_error}")
    print("=" * 70)
    pretty_print(tree.root_node, source, max_depth=max_depth)
    print()
    return tree, source


if __name__ == "__main__":
    # JS file: shallow depth is enough to see the shape (var decls, jQuery calls, prototype methods)
    parse_file(SAMPLES_DIR / "legacy_jquery.js", "javascript", max_depth=4)

    # Python 2 file: same idea
    parse_file(SAMPLES_DIR / "legacy_python2.py", "python", max_depth=4)
