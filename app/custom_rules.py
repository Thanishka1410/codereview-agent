import re
from pathlib import Path
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from app.ai.base import ReviewIssue


class CustomRule(BaseModel):
    """Defines a user-configurable static analysis rule."""
    id: str = Field(description="Unique rule identifier (e.g. 'no-hardcoded-ip')")
    category: str = Field(default="Custom", description="Issue category (Security, Quality, Architecture, etc.)")
    severity: str = Field(default="MEDIUM", description="Severity level: HIGH, MEDIUM, LOW, INFO")
    title: str = Field(description="Short human-readable finding title")
    pattern: str = Field(description="Regex pattern to match against source code")
    message: str = Field(description="Description of the issue detected")
    suggestion: str = Field(description="Actionable fix recommendation")
    code_example: Optional[str] = Field(default=None, description="Suggested code fix example")
    languages: List[str] = Field(default_factory=list, description="Target languages (empty matches all)")


class CustomRulesEngine:
    """Engine that executes user-defined regex rules loaded from configuration."""

    def __init__(self, rules: Optional[List[CustomRule]] = None):
        self.rules: List[CustomRule] = rules or []

    def evaluate_file(self, code: str, lines: List[str], relative_path: str, language: str) -> List[ReviewIssue]:
        """Evaluate a file against all configured custom rules."""
        issues: List[ReviewIssue] = []
        if not self.rules:
            return issues

        for rule in self.rules:
            # Check language filter
            if rule.languages and language.lower() not in [l.lower() for l in rule.languages]:
                continue

            try:
                compiled = re.compile(rule.pattern, re.IGNORECASE)
                for idx, line in enumerate(lines, start=1):
                    if compiled.search(line):
                        issues.append(
                            ReviewIssue(
                                severity=rule.severity.upper(),
                                category=rule.category,
                                file_path=relative_path,
                                line_number=idx,
                                title=rule.title,
                                description=rule.message,
                                suggestion=rule.suggestion,
                                code_example=rule.code_example,
                                confidence_score=0.90,
                                estimated_fix_minutes=15,
                            )
                        )
                        break  # Report once per file per rule
            except re.error:
                continue

        return issues
