import os
import sys
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field
from app.custom_rules import CustomRule

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


class ReviewConfig(BaseModel):
    """Data model for CodeReview Agent Configuration."""
    provider: str = Field(default="mock", description="AI Provider: openai, gemini, claude, mock")
    model: str = Field(default="gpt-4o", description="Model name to use")
    api_key: Optional[str] = Field(default=None, description="API Key for selected AI provider")
    temperature: float = Field(default=0.2, description="Sampling temperature")
    max_tokens: int = Field(default=2000, description="Max response tokens")
    language: str = Field(default="auto", description="Target language filter or auto")

    ignored_folders: List[str] = Field(
        default_factory=lambda: [
            ".git", "venv", ".venv", "node_modules", "dist", "build",
            "__pycache__", ".pytest_cache", ".egg-info", ".idea", ".vscode", "reports"
        ]
    )
    ignored_files: List[str] = Field(
        default_factory=lambda: [
            "package-lock.json", "yarn.lock", "poetry.lock", "Pipfile.lock"
        ]
    )
    max_file_size_kb: int = Field(default=500, description="Max file size in KB to scan")
    target_score: float = Field(default=8.5, description="Target minimum health score")
    fail_on_high_severity: bool = Field(default=False, description="Fail CLI exit code on high severity")
    use_rag: bool = Field(default=False, description="Enable RAG context indexing")
    docs_dir: Optional[str] = Field(default=None, description="Path to documentation folder for RAG")
    verbose: bool = Field(default=False, description="Enable verbose logging output")
    custom_rules: List[CustomRule] = Field(default_factory=list, description="User-defined custom static analysis rules")


def _parse_custom_rules_from_dict(file_data: dict) -> List[CustomRule]:
    """Parse custom rules array from configuration dictionary."""
    rules_sec = file_data.get("rules", {})
    raw_rules = []
    if isinstance(rules_sec, dict) and "custom" in rules_sec:
        raw_rules = rules_sec["custom"]
    elif "custom_rules" in file_data:
        raw_rules = file_data["custom_rules"]

    if not isinstance(raw_rules, list):
        return []

    return [CustomRule(**item) for item in raw_rules if isinstance(item, dict)]


def load_config(config_path: Optional[str] = None) -> ReviewConfig:
    """
    Load configuration by merging defaults, configuration files (.codereview.toml),
    and environment variables.
    """
    config_dict = {}

    paths_to_check = []
    if config_path:
        paths_to_check.append(Path(config_path))
    paths_to_check.extend([
        Path.cwd() / ".codereview.toml",
        Path.home() / ".codereview.toml"
    ])

    for path in paths_to_check:
        if not path.is_file():
            continue
        try:
            with open(path, "rb") as f:
                file_data = tomllib.load(f)
                config_dict.update(file_data.get("codereview", {}))
                config_dict.update(file_data.get("review", {}))
                custom_rules = _parse_custom_rules_from_dict(file_data)
                if custom_rules:
                    config_dict["custom_rules"] = custom_rules
            break
        except Exception as e:
            print(f"Warning: Failed to parse config file at {path}: {e}", file=sys.stderr)

    if os.getenv("CODEREVIEW_PROVIDER"):
        config_dict["provider"] = os.getenv("CODEREVIEW_PROVIDER")
    if os.getenv("CODEREVIEW_MODEL"):
        config_dict["model"] = os.getenv("CODEREVIEW_MODEL")
    if os.getenv("OPENAI_API_KEY"):
        if config_dict.get("provider") == "openai" or not config_dict.get("api_key"):
            config_dict["api_key"] = os.getenv("OPENAI_API_KEY")
    if os.getenv("GEMINI_API_KEY"):
        if config_dict.get("provider") == "gemini":
            config_dict["api_key"] = os.getenv("GEMINI_API_KEY")
    if os.getenv("ANTHROPIC_API_KEY"):
        if config_dict.get("provider") == "claude":
            config_dict["api_key"] = os.getenv("ANTHROPIC_API_KEY")

    return ReviewConfig(**config_dict)
