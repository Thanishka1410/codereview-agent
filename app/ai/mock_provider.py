import json
import re
from typing import List, Optional
from app.ai.base import BaseAIProvider, AIResponse, ReviewIssue
from app.prompts import SYSTEM_PROMPT, GENERAL_REVIEW_PROMPT, SECURITY_REVIEW_PROMPT, PERFORMANCE_REVIEW_PROMPT


class MockAIProvider(BaseAIProvider):
    """
    Offline Mock AI Provider. Generates realistic, static security, quality,
    and performance review analysis without calling external APIs.
    Used for local testing, demo mode, and keyless operation.
    """

    def review_code(
        self,
        file_path: str,
        code: str,
        language: str,
        prompt_type: str = "general",
        functions: Optional[List[str]] = None,
        classes: Optional[List[str]] = None,
    ) -> AIResponse:
        issues: List[ReviewIssue] = []

        code_lower = code.lower()

        # 1. Security Checks (Mock Rules)
        if "select " in code_lower and (" + " in code_lower or " % " in code_lower or "format(" in code_lower or "f\"" in code_lower or "f'" in code_lower):
            issues.append(
                ReviewIssue(
                    severity="HIGH",
                    file_path=file_path,
                    line_number=self._find_line_number(code, ["select", "from", "where"]),
                    category="Security",
                    title="Potential SQL Injection",
                    description="String concatenation or interpolation detected in SQL query construction.",
                    suggestion="Use parameterized queries or ORM bindings (e.g., cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))).",
                )
            )

        if any(secret_word in code_lower for secret_word in ["api_key =", "password =", "secret =", "token =", "private_key ="]):
            issues.append(
                ReviewIssue(
                    severity="HIGH",
                    file_path=file_path,
                    line_number=self._find_line_number(code, ["api_key", "password", "secret", "token"]),
                    category="Security",
                    title="Hardcoded Credentials / Secret",
                    description="Sensitive secret, API key, or password appears to be hardcoded in source file.",
                    suggestion="Move secret to environment variables (`os.getenv(...)`) or external secret manager.",
                )
            )

        if "eval(" in code_lower or "exec(" in code_lower:
            issues.append(
                ReviewIssue(
                    severity="HIGH",
                    file_path=file_path,
                    line_number=self._find_line_number(code, ["eval", "exec"]),
                    category="Security",
                    title="Dynamic Code Execution (eval/exec)",
                    description="Use of eval() or exec() can allow arbitrary code execution vulnerabilities.",
                    suggestion="Replace dynamic code execution with safe dictionary mapping or ast.literal_eval.",
                )
            )

        # 2. Performance & Code Smell Checks
        if "except:" in code or "except Exception:" in code and "pass" in code:
            issues.append(
                ReviewIssue(
                    severity="MEDIUM",
                    file_path=file_path,
                    line_number=self._find_line_number(code, ["except", "pass"]),
                    category="Bug",
                    title="Silently Swallowed Exception",
                    description="Broad exception handler with 'pass' hides runtime errors and makes debugging extremely difficult.",
                    suggestion="Catch specific exception types and log the exception details properly.",
                )
            )

        if "open(" in code_lower and "with " not in code_lower:
            issues.append(
                ReviewIssue(
                    severity="MEDIUM",
                    file_path=file_path,
                    line_number=self._find_line_number(code, ["open("]),
                    category="Performance",
                    title="Unclosed File Resource",
                    description="File opened without context manager ('with' statement) may leak file descriptors.",
                    suggestion="Use 'with open(...) as f:' context manager to ensure safe resource cleanup.",
                )
            )

        # 3. Readability & Code Quality Checks
        lines = code.splitlines()
        for idx, line in enumerate(lines, start=1):
            if len(line.strip()) == 1 and line.strip() in ("x", "y", "tmp", "temp", "a", "b", "d"):
                issues.append(
                    ReviewIssue(
                        severity="LOW",
                        file_path=file_path,
                        line_number=idx,
                        category="Readability",
                        title=f"Non-descriptive variable name '{line.strip()}'",
                        description=f"Variable name '{line.strip()}' lacks domain context and clear intent.",
                        suggestion=f"Rename '{line.strip()}' to a descriptive identifier reflecting its purpose.",
                    )
                )
                break

        if len(lines) > 200:
            issues.append(
                ReviewIssue(
                    severity="INFO",
                    file_path=file_path,
                    line_number=1,
                    category="Architecture",
                    title="Large Source File (>200 lines)",
                    description=f"File has {len(lines)} lines of code. Large files violate Single Responsibility Principle.",
                    suggestion="Consider refactoring into smaller modular components or helper utilities.",
                )
            )

        if not issues:
            issues.append(
                ReviewIssue(
                    severity="INFO",
                    file_path=file_path,
                    line_number=1,
                    category="Readability",
                    title="Clean Code Structure",
                    description="Code adheres well to syntax and general formatting standard guidelines.",
                    suggestion="Maintain good unit test coverage and modular documentation.",
                )
            )

        summary = f"Scanned file {file_path} ({len(lines)} lines). Identified {len(issues)} code review observation(s)."

        return AIResponse(
            issues=issues,
            summary=summary,
            provider_name="Mock (Offline)",
            model_name="rule-engine-v1",
        )

    def _find_line_number(self, code: str, keywords: List[str]) -> Optional[int]:
        lines = code.splitlines()
        for idx, line in enumerate(lines, start=1):
            line_low = line.lower()
            if any(kw in line_low for kw in keywords):
                return idx
        return 1
