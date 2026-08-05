import ast
import re
from pathlib import Path
from typing import List, Optional
from app.ai.base import ReviewIssue


class StaticAnalyzer:
    """
    Production-Grade Rule-Based Static Analysis Engine.
    Executes AST and regex-based checks for Security, Quality, Performance, and Architecture.
    """

    def analyze_file(self, file_path: Path, relative_path: str, code: str, language: str) -> List[ReviewIssue]:
        """Analyze a single source file against static security and quality rules."""
        # Skip meta rule files, mock definitions, templates, markdown docs, and test fixtures
        path_lower = relative_path.lower()
        if (
            "static_analysis" in path_lower
            or "mock_provider" in path_lower
            or "templates" in path_lower
            or path_lower.endswith(".md")
            or "examples" in path_lower
            or "tests" in path_lower
        ):
            return []

        issues: List[ReviewIssue] = []
        norm_path = relative_path.replace("\\", "/").lower()

        # Exclude mock engine, test fixtures, and report outputs from rule self-matching
        if any(p in norm_path for p in ["mock_provider.py", "examples/", "tests/", "reports/"]):
            return issues

        lines = code.splitlines()

        # 1. Security Analysis Rules
        issues.extend(self._check_security_rules(code, lines, relative_path, language))

        # 2. Quality Analysis Rules
        issues.extend(self._check_quality_rules(code, lines, relative_path, language))

        # 3. Performance Analysis Rules
        issues.extend(self._check_performance_rules(code, lines, relative_path, language))

        # 4. Architecture Rules
        issues.extend(self._check_architecture_rules(lines, relative_path, language))

        return issues

    def _find_line_number(self, lines: List[str], regex_pattern: str) -> Optional[int]:
        """Find matching line number for regex pattern."""
        compiled = re.compile(regex_pattern, re.IGNORECASE)
        for idx, line in enumerate(lines, start=1):
            if compiled.search(line):
                return idx
        return 1

    def _check_security_rules(self, code: str, lines: List[str], relative_path: str, language: str) -> List[ReviewIssue]:
        issues: List[ReviewIssue] = []
        code_lower = code.lower()

        # SQL Injection
        sql_patterns = [
            r'SELECT\s+.*?\s+FROM\s+.*?\+\s*',
            r'cursor\.execute\s*\(\s*f["\']',
            r'cursor\.execute\s*\(\s*["\'].*?%s.*?["\']\s*%',
            r'SELECT\s+.*?\s+WHERE\s+.*?\+\s*',
        ]
        for pat in sql_patterns:
            if re.search(pat, code, re.IGNORECASE):
                line_no = self._find_line_number(lines, pat)
                issues.append(
                    ReviewIssue(
                        severity="HIGH",
                        category="Security",
                        file_path=relative_path,
                        line_number=line_no,
                        title="Potential SQL Injection Vulnerability",
                        description="String concatenation or f-string interpolation detected inside SQL query string.",
                        suggestion="Use parameterized query placeholders or ORM bindings (e.g. cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))).",
                        code_example="cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))",
                        confidence_score=0.95,
                        estimated_fix_minutes=20,
                    )
                )
                break

        # Command Injection & Dangerous Subprocess
        if "subprocess" in code_lower and ("shell=true" in code_lower or "shell = true" in code_lower):
            line_no = self._find_line_number(lines, r'shell\s*=\s*True')
            issues.append(
                ReviewIssue(
                    severity="HIGH",
                    category="Security",
                    file_path=relative_path,
                    line_number=line_no,
                    title="Dangerous Subprocess Execution (shell=True)",
                    description="Executing shell commands with shell=True invites Command Injection vulnerabilities if arguments are unformatted.",
                    suggestion="Set shell=False and pass arguments as a list of strings: subprocess.run(['ls', '-l']).",
                    code_example="subprocess.run(['ls', '-la'], check=True)",
                    confidence_score=0.98,
                    estimated_fix_minutes=15,
                )
            )

        if "os.system(" in code_lower:
            line_no = self._find_line_number(lines, r'os\.system\(')
            issues.append(
                ReviewIssue(
                    severity="HIGH",
                    category="Security",
                    file_path=relative_path,
                    line_number=line_no,
                    title="Unsafe OS Command Execution (os.system)",
                    description="os.system() passes input directly to shell without input validation.",
                    suggestion="Replace os.system() with subprocess.run() using array arguments.",
                    code_example="subprocess.run(['git', 'status'], check=True)",
                    confidence_score=0.95,
                    estimated_fix_minutes=15,
                )
            )

        # Hardcoded Credentials & Weak Passwords
        secret_pattern = r'\b(api_key|password|secret_key|private_key|auth_token)\s*=\s*["\'][^"\'\s]{6,}["\']'
        if re.search(secret_pattern, code, re.IGNORECASE):
            line_no = self._find_line_number(lines, secret_pattern)
            issues.append(
                ReviewIssue(
                    severity="HIGH",
                    category="Security",
                    file_path=relative_path,
                    line_number=line_no,
                    title="Hardcoded Credential or API Secret",
                    description="Plaintext password, API key, or secret token detected in source code.",
                    suggestion="Store secrets in environment variables (os.environ) or an external secret manager.",
                    code_example="api_key = os.getenv('API_KEY')",
                    confidence_score=0.90,
                    estimated_fix_minutes=15,
                )
            )

        # Unsafe eval / exec
        if "eval(" in code_lower or "exec(" in code_lower:
            line_no = self._find_line_number(lines, r'\b(eval|exec)\(')
            issues.append(
                ReviewIssue(
                    severity="HIGH",
                    category="Security",
                    file_path=relative_path,
                    line_number=line_no,
                    title="Unsafe Code Execution (eval/exec)",
                    description="Dynamic code evaluation using eval() or exec() allows arbitrary code execution.",
                    suggestion="Replace eval() with ast.literal_eval() for safe literal evaluation or dictionary lookup.",
                    code_example="import ast; value = ast.literal_eval(user_input)",
                    confidence_score=0.95,
                    estimated_fix_minutes=25,
                )
            )

        # Unsafe Deserialization
        if "pickle.loads(" in code_lower or "yaml.unsafe_load(" in code_lower:
            line_no = self._find_line_number(lines, r'(pickle\.loads|yaml\.unsafe_load)')
            issues.append(
                ReviewIssue(
                    severity="HIGH",
                    category="Security",
                    file_path=relative_path,
                    line_number=line_no,
                    title="Unsafe Object Deserialization",
                    description="Deserializing untrusted data with pickle or yaml.unsafe_load can execute arbitrary python code.",
                    suggestion="Use safe serialization formats like JSON or yaml.safe_load().",
                    code_example="data = json.loads(json_string)",
                    confidence_score=0.95,
                    estimated_fix_minutes=30,
                )
            )

        # XSS Vulnerability (JS/TS/React)
        if language in ("javascript", "typescript", "react", "html") and ("innerhtml" in code_lower or "document.write" in code_lower or "dangerouslysetinnerhtml" in code_lower):
            line_no = self._find_line_number(lines, r'(innerHTML|document\.write|dangerouslySetInnerHTML)')
            issues.append(
                ReviewIssue(
                    severity="HIGH",
                    category="Security",
                    file_path=relative_path,
                    line_number=line_no,
                    title="Potential Cross-Site Scripting (XSS)",
                    description="Direct DOM insertion using innerHTML or document.write allows unescaped script injection.",
                    suggestion="Use element.textContent or safe DOM manipulation frameworks.",
                    code_example="element.textContent = userContent;",
                    confidence_score=0.90,
                    estimated_fix_minutes=20,
                )
            )

        return issues

    def _check_quality_rules(self, code: str, lines: List[str], relative_path: str, language: str) -> List[ReviewIssue]:
        issues: List[ReviewIssue] = []

        # Deep Nesting Rule (>5 indentation levels)
        for idx, line in enumerate(lines, start=1):
            indent_level = (len(line) - len(line.lstrip(' '))) // 4
            if indent_level >= 6 and not line.strip().startswith("#") and not line.strip().startswith("//") and not line.strip().startswith('"""'):
                issues.append(
                    ReviewIssue(
                        severity="MEDIUM",
                        category="Quality",
                        file_path=relative_path,
                        line_number=idx,
                        title=f"Deep Nesting Level ({indent_level} levels)",
                        description=f"Deeply nested code block at line {idx} reduces readability and increases cognitive complexity.",
                        suggestion="Refactor nested conditionals using guard clauses or break logic into helper functions.",
                        code_example="if not condition:\n    return\n# Main logic continues here",
                        confidence_score=0.85,
                        estimated_fix_minutes=25,
                    )
                )
                break

        # Swallowed Exceptions (consecutive except block with pass)
        swallowed_pattern = r'except\s*.*:\s*\n\s*pass\b'
        if re.search(swallowed_pattern, code):
            line_no = self._find_line_number(lines, r'except\s*.*:\s*\n\s*pass')
            issues.append(
                ReviewIssue(
                    severity="MEDIUM",
                    category="Quality",
                    file_path=relative_path,
                    line_number=line_no,
                    title="Silently Swallowed Exception",
                    description="Broad exception block with 'pass' hides unexpected errors during execution.",
                    suggestion="Catch specific exception types and log error details.",
                    code_example="except ValueError as e:\n    logger.error(f'Validation error: {e}')",
                    confidence_score=0.90,
                    estimated_fix_minutes=15,
                )
            )

        return issues

    def _check_performance_rules(self, code: str, lines: List[str], relative_path: str, language: str) -> List[ReviewIssue]:
        issues: List[ReviewIssue] = []

        # Nested Loops (O(n^2) complexity)
        nested_loop_pattern = r'(for|while)\s+.*?:[^\n]*?\n(?:\s*#[^\n]*?\n)*?\s+(for|while)\s+.*?:'
        if re.search(nested_loop_pattern, code):
            line_no = self._find_line_number(lines, r'(for|while)\s+.*?:')
            issues.append(
                ReviewIssue(
                    severity="MEDIUM",
                    category="Performance",
                    file_path=relative_path,
                    line_number=line_no,
                    title="Nested Loop Detected (O(n²) Complexity)",
                    description="Nested loop can significantly degrade runtime performance on large datasets.",
                    suggestion="Use set lookups, dictionary mapping, or vectorized operations to reduce quadratic complexity to O(n).",
                    code_example="lookup_set = set(list_b)\nresult = [item for item in list_a if item in lookup_set]",
                    confidence_score=0.85,
                    estimated_fix_minutes=30,
                )
            )

        return issues

    def _check_architecture_rules(self, lines: List[str], relative_path: str, language: str) -> List[ReviewIssue]:
        issues: List[ReviewIssue] = []

        is_doc = any(relative_path.endswith(ext) for ext in [".md", ".txt", ".rst", ".json", ".html"])
        if not is_doc and len(lines) > 350:
            issues.append(
                ReviewIssue(
                    severity="INFO",
                    category="Architecture",
                    file_path=relative_path,
                    line_number=1,
                    title=f"Large Source File ({len(lines)} lines)",
                    description=f"File contains {len(lines)} lines of code, exceeding modular guideline of 350 lines.",
                    suggestion="Decompose file into focused sub-modules or utility helper classes adhering to SRP.",
                    confidence_score=0.75,
                    estimated_fix_minutes=45,
                )
            )

        return issues
