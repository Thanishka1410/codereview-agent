from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel, Field


class ReviewIssue(BaseModel):
    """Represents an individual issue identified during AI code review."""
    severity: str = Field(description="Severity level: HIGH, MEDIUM, LOW, INFO")
    file_path: str = Field(description="Relative path to file")
    line_number: Optional[int] = Field(default=None, description="Line number of issue if applicable")
    category: str = Field(default="General", description="Category: Security, Bug, Performance, Readability, Architecture")
    title: str = Field(description="Title of the issue")
    description: str = Field(description="Detailed explanation")
    suggestion: str = Field(description="Actionable fix or refactoring advice")


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
        """
        Send code snippet to AI provider and parse JSON issue response.
        """
        pass
