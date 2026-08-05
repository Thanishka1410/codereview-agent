import json
from typing import List, Optional
import requests
from app.ai.base import BaseAIProvider, AIResponse, ReviewIssue, repair_json_text
from app.prompts import SYSTEM_PROMPT, GENERAL_REVIEW_PROMPT, SECURITY_REVIEW_PROMPT, PERFORMANCE_REVIEW_PROMPT


class GeminiProvider(BaseAIProvider):
    """
    Google Gemini Provider using REST API endpoints.
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
            raise ValueError("Gemini API Key is missing. Set GEMINI_API_KEY environment variable or config.")

        model_name = self.model if self.model and "gemini" in self.model else "gemini-1.5-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.api_key}"

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

        full_prompt = f"{SYSTEM_PROMPT}\n\n{user_content}"

        payload = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_tokens,
                "responseMimeType": "application/json",
            },
        }

        try:
            response = requests.post(url, json=payload, timeout=45)
            response.raise_for_status()
            data = response.json()

            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
            return self._parse_json_response(raw_text, file_path, model_name)

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Gemini API request failed: {e}")

    def _parse_json_response(self, raw_text: str, file_path: str, model_name: str) -> AIResponse:
        clean_text = repair_json_text(raw_text)

        try:
            parsed = json.loads(clean_text)
            issues_data = parsed.get("issues", [])
            summary = parsed.get("summary", "Review complete.")

            issues: List[ReviewIssue] = []
            for item in issues_data:
                issues.append(
                    ReviewIssue(
                        severity=str(item.get("severity", "MEDIUM")).upper(),
                        category=item.get("category", "General"),
                        file_path=item.get("file_path", file_path),
                        line_number=item.get("line_number"),
                        title=item.get("title", "Review Finding"),
                        description=item.get("description", ""),
                        suggestion=item.get("suggestion", ""),
                        code_example=item.get("code_example"),
                        confidence_score=float(item.get("confidence_score", 0.9)),
                        estimated_fix_minutes=int(item.get("estimated_fix_minutes", 15)),
                    )
                )

            return AIResponse(
                issues=issues,
                summary=summary,
                raw_response=raw_text,
                provider_name="Gemini",
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
                summary="Gemini raw output parsed.",
                raw_response=raw_text,
                provider_name="Gemini",
                model_name=model_name,
            )
