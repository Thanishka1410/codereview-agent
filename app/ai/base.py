"""
Abstract base class and data models for AI Code Review Providers and findings.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel, Field


class ReviewIssue(BaseModel):
    """Represents an individual issue identified during static analysis or AI code review."""
    severity: str = Field(description="Severity level: HIGH, MEDIUM, LOW, INFO")
    category: str = Field(default="General", description="Category: Security, Bug, Performance, Readability, Architecture, Quality")
    file_path: str = Field(description="Relative path to file")
    line_number: Optional[int] = Field(default=None, description="Line number of issue if applicable")
    title: str = Field(description="Short descriptive title of the issue")
    description: str = Field(description="Detailed explanation of the problem")
    suggestion: str = Field(description="Actionable fix or refactoring advice")
    code_example: Optional[str] = Field(default=None, description="Corrected code snippet example")
    confidence_score: float = Field(default=0.9, description="Confidence score from 0.0 to 1.0")
    estimated_fix_minutes: int = Field(default=15, description="Estimated time to fix in minutes")


class AIResponse(BaseModel):
    """Encapsulates the result returned by an AI Provider."""
    issues: List[ReviewIssue]
    summary: str
    raw_response: Optional[str] = None
    provider_name: str
    model_name: str


class BaseAIProvider(ABC):
    """Abstract Base Class for AI Code Review Providers."""

    def __init__(self, api_key: Optional[str] = None, model: str = "default", temperature: float = 0.2, max_tokens: int = 2000):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    @abstractmethod
    def review_code(
        self,
        file_path: str,
        code: str,
        language: str,
        prompt_type: str = "general",
        functions: Optional[List[str]] = None,
        classes: Optional[List[str]] = None,
    ) -> AIResponse:
        """Send code snippet to AI provider and parse JSON issue response."""
        pass


def build_review_issue_from_dict(item: dict, default_path: str) -> ReviewIssue:
    """Construct ReviewIssue model from raw dictionary payload."""
    return ReviewIssue(
        severity=str(item.get("severity", "MEDIUM")).upper(),
        category=item.get("category", "General"),
        file_path=item.get("file_path", default_path),
        line_number=item.get("line_number"),
        title=item.get("title", "Review Finding"),
        description=item.get("description", ""),
        suggestion=item.get("suggestion", ""),
        code_example=item.get("code_example"),
        confidence_score=float(item.get("confidence_score", 0.9)),
        estimated_fix_minutes=int(item.get("estimated_fix_minutes", 15)),
    )
def repair_json_text(raw_text: str) -> str:
    """Utility function to clean and repair malformed JSON string from LLM responses."""
    clean_text = raw_text.strip()
    if clean_text.startswith("```json"):
        clean_text = clean_text[7:]
    if clean_text.startswith("```"):
        clean_text = clean_text[3:]
    if clean_text.endswith("```"):
        clean_text = clean_text[:-3]
    clean_text = clean_text.strip()

    # Attempt to extract first '{' and last '}'
    first_brace = clean_text.find("{")
    last_brace = clean_text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        clean_text = clean_text[first_brace:last_brace + 1]

    return clean_text
