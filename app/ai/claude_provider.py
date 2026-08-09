"""
Anthropic Claude AI Provider implementation for CodeReview Agent.
"""

import json
from typing import List, Optional
import requests
from app.ai.base import BaseAIProvider, AIResponse, ReviewIssue, repair_json_text, build_review_issue_from_dict
from app.prompts import SYSTEM_PROMPT, GENERAL_REVIEW_PROMPT, SECURITY_REVIEW_PROMPT, PERFORMANCE_REVIEW_PROMPT


class ClaudeProvider(BaseAIProvider):
    """
    Anthropic Claude Provider supporting Claude 3.5 Sonnet / Haiku via REST API.
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
        if not self.api_key:
            raise ValueError("Anthropic API Key is missing. Set ANTHROPIC_API_KEY environment variable or config.")

        model_name = self.model if self.model and "claude" in self.model else "claude-3-5-sonnet-20240620"
        url = "https://api.anthropic.com/v1/messages"

        if prompt_type == "security":
            prompt_template = SECURITY_REVIEW_PROMPT
        elif prompt_type == "performance":
            prompt_template = PERFORMANCE_REVIEW_PROMPT
        else:
            prompt_template = GENERAL_REVIEW_PROMPT

        user_content = prompt_template.format(
            file_path=file_path,
            language=language,
            code=code,
            functions=", ".join(functions) if functions else "None",
            classes=", ".join(classes) if classes else "None",
        )

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        payload = {
            "model": model_name,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": user_content}],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=45)
            response.raise_for_status()
            data = response.json()

            raw_text = data["content"][0]["text"]
            return self._parse_json_response(raw_text, file_path, model_name)

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Claude API request failed: {e}")

    def _parse_json_response(self, raw_text: str, file_path: str, model_name: str) -> AIResponse:
        clean_text = repair_json_text(raw_text)

        try:
            parsed = json.loads(clean_text)
            issues_data = parsed.get("issues", [])
            summary = parsed.get("summary", "Review complete.")

            issues: List[ReviewIssue] = [build_review_issue_from_dict(item, file_path) for item in issues_data]

            return AIResponse(
                issues=issues,
                summary=summary,
                raw_response=raw_text,
                provider_name="Claude",
                model_name=model_name,
            )
        except Exception:
            return AIResponse(
                issues=[
                    ReviewIssue(
                        severity="INFO",
                        category="General",
                        file_path=file_path,
                        title="AI Analysis Output",
                        description=raw_text[:300],
                        suggestion="Check raw response.",
                    )
                ],
                summary="Claude raw output parsed.",
                raw_response=raw_text,
                provider_name="Claude",
                model_name=model_name,
            )
