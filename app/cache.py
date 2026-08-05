import hashlib
import json
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class CacheEntry(BaseModel):
    """Represents cached scan metadata for a single file."""
    file_path: str
    sha256: str
    issues: list[dict] = Field(default_factory=list)


class FileCacheManager:
    """Manages SHA-256 hash caching for incremental codebase reviews."""

    def __init__(self, cache_file: Optional[Path] = None):
        self.cache_file = cache_file or (Path.cwd() / ".codereview_cache.json")
        self.cache: Dict[str, CacheEntry] = {}
        self.load_cache()

    def _compute_hash(self, file_path: Path) -> str:
        """Compute SHA-256 hash of a file."""
        hasher = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception:
            return ""

    def load_cache(self):
        """Load cache from JSON file."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for k, v in data.items():
                        self.cache[k] = CacheEntry(**v)
            except Exception:
                self.cache = {}

    def save_cache(self):
        """Save cache to JSON file."""
        try:
            data = {k: v.model_dump() for k, v in self.cache.items()}
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def is_file_unchanged(self, file_path: Path, relative_path: str) -> bool:
        """Check if file hash matches cached hash."""
        if relative_path not in self.cache:
            return False
        current_hash = self._compute_hash(file_path)
        return self.cache[relative_path].sha256 == current_hash and current_hash != ""

    def get_cached_issues(self, relative_path: str) -> list[dict]:
        """Retrieve cached issues for unchanged file."""
        if relative_path in self.cache:
            return self.cache[relative_path].issues
        return []

    def update_cache(self, file_path: Path, relative_path: str, issues: list[Any]):
        """Update cache entry for file."""
        current_hash = self._compute_hash(file_path)
        if current_hash:
            issues_dict = [i.model_dump() if hasattr(i, "model_dump") else i for i in issues]
            self.cache[relative_path] = CacheEntry(
                file_path=relative_path,
                sha256=current_hash,
                issues=issues_dict,
            )
