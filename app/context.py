import ast
from typing import List, Dict, Optional


class CodeContextBuilder:
    """
    Summarizes large files and constructs AST context representations
    to prevent LLM context window overflow while preserving structural logic.
    """

    def summarize_code(self, code: str, language: str, max_chars: int = 4000) -> str:
        """Truncate or summarize code if it exceeds character limits."""
        if len(code) <= max_chars:
            return code

        lines = code.splitlines()
        header_lines = lines[:50]
        footer_lines = lines[-50:]
        omitted_count = len(lines) - 100

        return "\n".join(header_lines) + f"\n\n... [{omitted_count} lines omitted for context size optimization] ...\n\n" + "\n".join(footer_lines)

    def extract_python_signatures(self, code: str) -> str:
        """Extract high-level Python function and class signatures using AST."""
        signatures: List[str] = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    signatures.append(f"class {node.name}:")
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    args_list = [arg.arg for arg in node.args.args]
                    signatures.append(f"def {node.name}({', '.join(args_list)}):")
        except Exception:
            pass

        return "\n".join(signatures) if signatures else "No explicit signatures extracted."
