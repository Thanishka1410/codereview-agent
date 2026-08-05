import os
import sys
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field

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


def load_config(config_path: Optional[str] = None) -> ReviewConfig:
    """
    Load configuration by merging defaults, configuration files (.codereview.toml),
    and environment variables.
    """
    config_dict = {}

    # 1. Search for .codereview.toml in current directory or specified path
    paths_to_check = []
    if config_path:
        paths_to_check.append(Path(config_path))
    paths_to_check.extend([
        Path.cwd() / ".codereview.toml",
        Path.home() / ".codereview.toml"
    ])

    for path in paths_to_check:
        if path.is_file():
            try:
                with open(path, "rb") as f:
                    file_data = tomllib.load(f)
                    # Merge [codereview] and [review] sections
                    codereview_sec = file_data.get("codereview", {})
                    review_sec = file_data.get("review", {})
                    config_dict.update(codereview_sec)
                    config_dict.update(review_sec)
                break
            except Exception as e:
                print(f"Warning: Failed to parse config file at {path}: {e}", file=sys.stderr)

    # 2. Environment variable overrides
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
