"""
Local LLM provider integration for offline code review via Ollama REST API.
"""

import json
from typing import List, Optional
import requests
from app.ai.base import BaseAIProvider, AIResponse, ReviewIssue, repair_json_text, build_review_issue_from_dict
from app.prompts import SYSTEM_PROMPT, GENERAL_REVIEW_PROMPT, SECURITY_REVIEW_PROMPT, PERFORMANCE_REVIEW_PROMPT


class OllamaProvider(BaseAIProvider):
    """Local LLM AI Provider integration connecting to Ollama REST API endpoints."""

    def __init__(
        self,
        model: str = "deepseek-coder:6.7b",
        ollama_host: str = "http://localhost:11434",
        temperature: float = 0.2,
    ):
        self.model = model
        self.ollama_host = ollama_host.rstrip("/")
        self.temperature = temperature
        self.provider_name = "Ollama (Local LLM)"

    def review_code(
        self,
        file_path: str,
        code: str,
        language: str,
        prompt_type: str = "general",
        functions: Optional[List[str]] = None,
        classes: Optional[List[str]] = None,
    ) -> AIResponse:
        """Send code snippet to local Ollama API endpoint and parse JSON findings."""
        if prompt_type == "security":
            task_prompt = SECURITY_REVIEW_PROMPT
        elif prompt_type == "performance":
            task_prompt = PERFORMANCE_REVIEW_PROMPT
        else:
            task_prompt = GENERAL_REVIEW_PROMPT

        user_content = f"{task_prompt}\n\nFile: {file_path}\nLanguage: {language}\nFunctions: {functions or []}\nClasses: {classes or []}\n\nSource Code:\n```{language}\n{code}\n```"

        url = f"{self.ollama_host}/api/generate"
        payload = {
            "model": self.model,
            "prompt": f"{SYSTEM_PROMPT}\n\n{user_content}",
            "stream": False,
            "format": "json",
            "options": {
                "temperature": self.temperature,
            },
        }

        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()

            res_json = response.json()
            raw_text = res_json.get("response", "")
            return self._parse_json_response(raw_text, file_path)

        except requests.exceptions.RequestException as e:
            return AIResponse(
                issues=[],
                summary=f"Local Ollama connection failed ({self.ollama_host}): {e}",
                raw_response=str(e),
                provider_name=self.provider_name,
                model_name=self.model,
            )

    def _parse_json_response(self, raw_text: str, file_path: str) -> AIResponse:
        """Parse structured JSON from Ollama LLM response text."""
        cleaned_json = repair_json_text(raw_text)

        try:
            parsed = json.loads(cleaned_json)
            issues_data = parsed.get("issues", [])
            summary = parsed.get("summary", "Local LLM code review complete.")
            issues: List[ReviewIssue] = [build_review_issue_from_dict(item, file_path) for item in issues_data]

            return AIResponse(
                issues=issues,
                summary=summary,
                raw_response=raw_text,
                provider_name=self.provider_name,
                model_name=self.model,
            )

        except json.JSONDecodeError:
            return AIResponse(
                issues=[],
                summary="Failed to parse structured JSON from local Ollama model response.",
                raw_response=raw_text,
                provider_name=self.provider_name,
                model_name=self.model,
            )
