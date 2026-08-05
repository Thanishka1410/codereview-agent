import ast
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from pydantic import BaseModel


class FileStructureMetrics(BaseModel):
    """Detailed AST / structure analysis metrics of a source file."""
    relative_path: str
    language: str
    imports: List[str]
    functions: List[str]
    methods: List[str]
    classes: List[str]
    decorators: List[str]
    global_vars: List[str]
    has_docstring: bool
    loc: int
    complexity: int
    code_content: str


class GitInfo(BaseModel):
    """Git repository information and modified files."""
    is_git_repo: bool = False
    current_branch: Optional[str] = None
    modified_files: List[str] = []
    staged_files: List[str] = []
    changed_lines: Dict[str, List[int]] = {}


def calculate_python_complexity(node: ast.AST) -> int:
    """Calculate average Cyclomatic Complexity per function for Python AST node."""
    decisions = 1
    fn_count = 0
    for child in ast.walk(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            fn_count += 1
        elif isinstance(
            child,
            (
                ast.If,
                ast.For,
                ast.While,
                ast.AsyncFor,
                ast.ExceptHandler,
                ast.With,
                ast.AsyncWith,
                ast.Assert,
            ),
        ):
            decisions += 1
        elif isinstance(child, ast.BoolOp):
            decisions += len(child.values) - 1
        elif isinstance(child, ast.IfExp):
            decisions += 1
    return max(1, round(decisions / max(1, fn_count)))


def _process_ast_node(node: ast.AST, imports: List[str], functions: List[str], methods: List[str], classes: List[str], decorators: List[str], global_vars: List[str]):
    """Process individual AST node to extract structural code metrics."""
    if isinstance(node, ast.Import):
        for alias in node.names:
            imports.append(alias.name)
    elif isinstance(node, ast.ImportFrom):
        module = node.module or ""
        for alias in node.names:
            imports.append(f"{module}.{alias.name}" if module else alias.name)
    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        functions.append(node.name)
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                decorators.append(dec.id)
            elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name):
                decorators.append(dec.func.id)
    elif isinstance(node, ast.ClassDef):
        classes.append(node.name)
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append(f"{node.name}.{item.name}")
    elif isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name) and (target.id.isupper() or target.id.startswith("GLOBAL_")):
                global_vars.append(target.id)


def analyze_python_file(file_path: Path, relative_path: str, code: str) -> FileStructureMetrics:
    """Analyze Python file using ast module."""
    imports: List[str] = []
    functions: List[str] = []
    methods: List[str] = []
    classes: List[str] = []
    decorators: List[str] = []
    global_vars: List[str] = []
    has_docstring = False
    complexity = 1

    try:
        tree = ast.parse(code, filename=str(file_path))
        complexity = calculate_python_complexity(tree)
        doc = ast.get_docstring(tree)
        has_docstring = doc is not None and len(doc.strip()) > 0

        for node in ast.walk(tree):
            _process_ast_node(node, imports, functions, methods, classes, decorators, global_vars)

    except SyntaxError:
        imports, functions, classes, complexity = fallback_regex_analysis(code)

    loc = len([line for line in code.splitlines() if line.strip() and not line.strip().startswith("#")])

    return FileStructureMetrics(
        relative_path=relative_path,
        language="python",
        imports=sorted(list(set(imports))),
        functions=functions,
        methods=methods,
        classes=classes,
        decorators=sorted(list(set(decorators))),
        global_vars=sorted(list(set(global_vars))),
        has_docstring=has_docstring,
        loc=loc,
        complexity=complexity,
        code_content=code,
    )


def fallback_regex_analysis(code: str) -> tuple[List[str], List[str], List[str], int]:
    """Extract metrics for non-Python files using regex patterns."""
    imports: Set[str] = set()
    functions: List[str] = []
    classes: List[str] = []

    combined_imports = re.compile(r'(?:import\s+.*?;|from\s+[\w\.]+\s+import|require\s*\([\'"][^\'"]+[\'"]\)|#include\s+[<"][^>"]+[>"]|use\s+[\w\\:]+;)')
    for match in combined_imports.finditer(code):
        imports.add(match.group(0).strip())

    func_patterns = [
        r'\bdef\s+([a-zA-Z_]\w*)\s*\(',
        r'\bfunction\s+([a-zA-Z_]\w*)\s*\(',
        r'\bconst\s+([a-zA-Z_]\w*)\s*=\s*\([^)]*\)\s*=>',
        r'\b([a-zA-Z_]\w*)\s*\([^)]*\)\s*\{',
        r'\bfn\s+([a-zA-Z_]\w*)\s*\(',
        r'\bfunc\s+([a-zA-Z_]\w*)\s*\(',
    ]
    for pattern in func_patterns:
        for match in re.finditer(pattern, code):
            fn_name = match.group(1)
            if fn_name not in ("if", "for", "while", "switch", "catch"):
                functions.append(fn_name)

    class_patterns = [
        r'\bclass\s+([a-zA-Z_]\w*)',
        r'\bstruct\s+([a-zA-Z_]\w*)',
        r'\binterface\s+([a-zA-Z_]\w*)',
        r'\btype\s+([a-zA-Z_]\w*)\s*=\s*struct',
    ]
    for pattern in class_patterns:
        for match in re.finditer(pattern, code):
            classes.append(match.group(1))

    decision_keywords = len(re.findall(r'\b(if|else if|for|while|case|catch|\&\&|\|\|)\b', code))
    complexity = max(1, 1 + decision_keywords)

    return list(imports), functions, classes, complexity


def analyze_file_structure(file_path: Path, relative_path: str, language: str) -> FileStructureMetrics:
    """Analyze file structure according to its language."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            code = f.read()
    except Exception as e:
        code = f"// Error reading file: {e}"

    if language == "python":
        return analyze_python_file(file_path, relative_path, code)

    imports, functions, classes, complexity = fallback_regex_analysis(code)
    loc = len([line for line in code.splitlines() if line.strip()])

    return FileStructureMetrics(
        relative_path=relative_path,
        language=language,
        imports=imports,
        functions=functions,
        methods=[],
        classes=classes,
        decorators=[],
        global_vars=[],
        has_docstring=False,
        loc=loc,
        complexity=complexity,
        code_content=code,
    )


def get_git_info(cwd: Optional[Path] = None) -> GitInfo:
    """Retrieve git branch and modified files status."""
    working_dir = str(cwd) if cwd else "."
    try:
        is_git = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=working_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=3,
        )
        if is_git.returncode != 0:
            return GitInfo(is_git_repo=False)

        branch_proc = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=working_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=3,
        )
        branch = branch_proc.stdout.strip() or "HEAD"

        status_proc = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=working_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=3,
        )

        modified: List[str] = []
        staged: List[str] = []

        for line in status_proc.stdout.splitlines():
            if len(line) >= 3:
                x, y = line[0], line[1]
                filepath = line[3:].strip()
                if x in ("M", "A", "R"):
                    staged.append(filepath)
                if y in ("M", "?"):
                    modified.append(filepath)

        return GitInfo(
            is_git_repo=True,
            current_branch=branch,
            modified_files=list(set(modified)),
            staged_files=list(set(staged)),
            changed_lines={},
        )

    except Exception:
        return GitInfo(is_git_repo=False)
