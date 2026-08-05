import json
import re
from typing import List, Optional
import requests
from app.ai.base import BaseAIProvider, AIResponse, ReviewIssue, repair_json_text, build_review_issue_from_dict
from app.prompts import (
    SYSTEM_PROMPT,
    GENERAL_REVIEW_PROMPT,
    SECURITY_REVIEW_PROMPT,
    PERFORMANCE_REVIEW_PROMPT,
    RAG_AUGMENTED_REVIEW_PROMPT,
)


class OpenAIProvider(BaseAIProvider):
    """
    OpenAI Provider supporting GPT-4o / GPT-4 / GPT-3.5 models via REST API.
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
            raise ValueError("OpenAI API Key is missing. Set OPENAI_API_KEY environment variable or config.")

        if prompt_type == "security":
            prompt_template = SECURITY_REVIEW_PROMPT
        elif prompt_type == "performance":
            prompt_template = PERFORMANCE_REVIEW_PROMPT
        elif prompt_type == "rag":
            prompt_template = RAG_AUGMENTED_REVIEW_PROMPT
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
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model or "gpt-4o",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=45,
            )
            response.raise_for_status()
            data = response.json()
            raw_text = data["choices"][0]["message"]["content"]
            return self._parse_json_response(raw_text, file_path)

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"OpenAI API request failed: {e}")

    def _parse_json_response(self, raw_text: str, file_path: str) -> AIResponse:
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
                provider_name="OpenAI",
                model_name=self.model or "gpt-4o",
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
                        suggestion="Parse raw text manually.",
                    )
                ],
                summary="AI response parsed with fallback.",
                raw_response=raw_text,
                provider_name="OpenAI",
                model_name=self.model or "gpt-4o",
            )
