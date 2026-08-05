import os
from pathlib import Path
from typing import List, Dict, Optional, Set
from pydantic import BaseModel, ConfigDict

# Mapping of file extensions to canonical language names
EXTENSION_TO_LANGUAGE: Dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "react",
    ".ts": "typescript",
    ".tsx": "react-typescript",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".php": "php",
    ".html": "html",
    ".htm": "html",
    ".css": "css",
    ".json": "json",
    ".md": "markdown",
}


class ScannedFile(BaseModel):
    """Represents a scanned source file with basic metadata."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    path: Path
    relative_path: str
    extension: str
    language: str
    size_bytes: int
    line_count: int


class ProjectScanResult(BaseModel):
    """Represents the complete result of scanning a project directory or single file."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    root_path: Path
    files: List[ScannedFile]
    total_files: int
    total_lines: int
    total_size_bytes: int
    primary_language: str
    language_breakdown: Dict[str, int]



class Scanner:
    """Project Scanner that detects files, languages, and ignores excluded folders."""

    def __init__(
        self,
        ignored_folders: Optional[List[str]] = None,
        ignored_files: Optional[List[str]] = None,
        max_file_size_kb: int = 500,
        language_filter: Optional[str] = None,
    ):
        self.ignored_folders: Set[str] = set(
            ignored_folders
            or [
                ".git", "venv", ".venv", "node_modules", "dist", "build",
                "__pycache__", ".pytest_cache", ".egg-info", ".idea", ".vscode"
            ]
        )
        self.ignored_files: Set[str] = set(
            ignored_files
            or ["package-lock.json", "yarn.lock", "poetry.lock", "Pipfile.lock"]
        )
        self.max_file_size_bytes = max_file_size_kb * 1024
        self.language_filter = language_filter.lower() if language_filter and language_filter != "auto" else None

    def detect_language(self, file_path: Path) -> str:
        """Detect programming language based on file extension."""
        ext = file_path.suffix.lower()
        return EXTENSION_TO_LANGUAGE.get(ext, "unknown")

    def should_ignore(self, path: Path, root: Path) -> bool:
        """Check if a file or directory should be ignored during scan."""
        # Check filename/dirname against ignore lists
        if path.name in self.ignored_files or path.name in self.ignored_folders:
            return True

        # Check if any parent directory is in ignored_folders relative to root
        try:
            rel_parts = path.relative_to(root).parts
            for part in rel_parts:
                if part in self.ignored_folders:
                    return True
        except ValueError:
            # Path is not relative to root
            return False

        return False

    def scan_file(self, file_path: Path, root: Path) -> Optional[ScannedFile]:
        """Scan a single file and collect metadata."""
        if not file_path.is_file():
            return None

        if self.should_ignore(file_path, root):
            return None

        size_bytes = file_path.stat().st_size
        if size_bytes > self.max_file_size_bytes or size_bytes == 0:
            return None

        language = self.detect_language(file_path)
        if language == "unknown":
            return None

        if self.language_filter and language != self.language_filter:
            return None

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                line_count = sum(1 for _ in f)
        except Exception:
            line_count = 0

        rel_path = str(file_path.relative_to(root)) if file_path != root else file_path.name

        return ScannedFile(
            path=file_path.resolve(),
            relative_path=rel_path,
            extension=file_path.suffix.lower(),
            language=language,
            size_bytes=size_bytes,
            line_count=line_count,
        )

    def scan(self, target_path: str | Path) -> ProjectScanResult:
        """Scan a directory or single file recursively."""
        target = Path(target_path).resolve()
        if not target.exists():
            raise FileNotFoundError(f"Target path does not exist: {target}")

        scanned_files: List[ScannedFile] = []
        root = target if target.is_dir() else target.parent

        if target.is_file():
            scanned_file = self.scan_file(target, root)
            if scanned_file:
                scanned_files.append(scanned_file)
        else:
            for current_root, dirs, files in os.walk(target):
                # Filter directories in-place to prevent entering ignored folders
                dirs[:] = [d for d in dirs if d not in self.ignored_folders]

                for file in files:
                    file_path = Path(current_root) / file
                    scanned_file = self.scan_file(file_path, root)
                    if scanned_file:
                        scanned_files.append(scanned_file)

        # Calculate statistics
        total_files = len(scanned_files)
        total_lines = sum(f.line_count for f in scanned_files)
        total_size_bytes = sum(f.size_bytes for f in scanned_files)

        lang_counts: Dict[str, int] = {}
        for f in scanned_files:
            lang_counts[f.language] = lang_counts.get(f.language, 0) + 1

        primary_lang = "unknown"
        if lang_counts:
            primary_lang = max(lang_counts.items(), key=lambda x: x[1])[0]

        return ProjectScanResult(
            root_path=root,
            files=scanned_files,
            total_files=total_files,
            total_lines=total_lines,
            total_size_bytes=total_size_bytes,
            primary_language=primary_lang,
            language_breakdown=lang_counts,
        )
