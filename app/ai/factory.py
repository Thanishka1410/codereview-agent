import sys
from typing import Optional
from app.ai.base import BaseAIProvider
from app.ai.mock_provider import MockAIProvider
from app.ai.openai_provider import OpenAIProvider
from app.ai.gemini_provider import GeminiProvider
from app.ai.claude_provider import ClaudeProvider
from app.config import ReviewConfig


def get_ai_provider(config: ReviewConfig) -> BaseAIProvider:
    """
    Factory function to instantiate appropriate AI Provider.
    Falls back to Mock Provider if provider is set to 'mock' or API key is absent.
    """
    provider_name = config.provider.lower().strip()

    if provider_name == "mock":
        return MockAIProvider(model=config.model)

    if provider_name == "openai":
        if not config.api_key:
            print("Warning: No OpenAI API key provided. Falling back to Mock AI Provider.", file=sys.stderr)
            return MockAIProvider(model=config.model)
        return OpenAIProvider(
            api_key=config.api_key,
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )

    if provider_name == "gemini":
        if not config.api_key:
            print("Warning: No Gemini API key provided. Falling back to Mock AI Provider.", file=sys.stderr)
            return MockAIProvider(model=config.model)
        return GeminiProvider(
            api_key=config.api_key,
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )

    if provider_name in ("claude", "anthropic"):
        if not config.api_key:
            print("Warning: No Anthropic API key provided. Falling back to Mock AI Provider.", file=sys.stderr)
            return MockAIProvider(model=config.model)
        return ClaudeProvider(
            api_key=config.api_key,
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )

    # Default fallback
    print(f"Warning: Unknown AI Provider '{config.provider}'. Falling back to Mock AI Provider.", file=sys.stderr)
    return MockAIProvider(model=config.model)
