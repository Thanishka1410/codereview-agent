import os
import fnmatch
from concurrent.futures import ThreadPoolExecutor, as_completed
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
    ".kt": "kotlin",
    ".kts": "kotlin",
    ".swift": "swift",
    ".dart": "dart",
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
    """Production-grade file scanner with parallel walking, binary check, and glob filters."""

    def __init__(
        self,
        ignored_folders: Optional[List[str]] = None,
        ignored_files: Optional[List[str]] = None,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        max_file_size_kb: int = 500,
        language_filter: Optional[str] = None,
    ):
        self.ignored_folders: Set[str] = set(
            ignored_folders
            or [
                ".git", "venv", ".venv", "node_modules", "dist", "build",
                "__pycache__", ".pytest_cache", ".egg-info", ".idea", ".vscode", "reports"
            ]
        )
        self.ignored_files: Set[str] = set(
            ignored_files
            or ["package-lock.json", "yarn.lock", "poetry.lock", "Pipfile.lock"]
        )
        self.include_patterns = include_patterns or []
        self.exclude_patterns = exclude_patterns or []
        self.max_file_size_bytes = max_file_size_kb * 1024
        self.language_filter = language_filter.lower() if language_filter and language_filter != "auto" else None
        self.seen_realpaths: Set[str] = set()

    def is_binary(self, file_path: Path) -> bool:
        """Check if file is binary by inspecting null bytes in first 1024 bytes."""
        try:
            with open(file_path, "rb") as f:
                chunk = f.read(1024)
                if b"\x00" in chunk:
                    return True
        except Exception:
            return True
        return False

    def is_generated_code(self, file_path: Path) -> bool:
        """Check if file is auto-generated."""
        name = file_path.name.lower()
        if name.endswith(".min.js") or name.endswith(".min.css") or "bundle" in name:
            return True
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                first_lines = "".join([f.readline() for _ in range(5)]).lower()
                if "@generated" in first_lines or "auto-generated" in first_lines:
                    return True
        except Exception:
            pass
        return False

    def detect_language(self, file_path: Path) -> str:
        """Detect programming language based on file extension."""
        ext = file_path.suffix.lower()
        return EXTENSION_TO_LANGUAGE.get(ext, "unknown")

    def should_ignore(self, path: Path, root: Path) -> bool:
        """Check if file/folder should be ignored."""
        name = path.name

        # Hidden file or folder
        if name.startswith(".") and name not in (".", ".."):
            if name in self.ignored_folders or name in self.ignored_files:
                return True

        if name in self.ignored_files or name in self.ignored_folders:
            return True

        try:
            rel_parts = path.relative_to(root).parts
            for part in rel_parts:
                if part in self.ignored_folders or (part.startswith(".") and part not in (".", "..")):
                    return True
        except ValueError:
            return False

        # Exclude patterns
        if self.exclude_patterns:
            if any(fnmatch.fnmatch(name, pat) for pat in self.exclude_patterns):
                return True

        # Include patterns
        if self.include_patterns:
            if not any(fnmatch.fnmatch(name, pat) for pat in self.include_patterns):
                return True

        return False

    def scan_file(self, file_path: Path, root: Path) -> Optional[ScannedFile]:
        """Scan a single file and collect metadata."""
        if not file_path.is_file():
            return None

        # Check symlinks & realpaths to prevent duplicate scanning or infinite loops
        try:
            real_p = str(file_path.resolve())
            if real_p in self.seen_realpaths:
                return None
            self.seen_realpaths.add(real_p)
        except Exception:
            return None

        if self.should_ignore(file_path, root):
            return None

        size_bytes = file_path.stat().st_size
        if size_bytes > self.max_file_size_bytes or size_bytes == 0:
            return None

        if self.is_binary(file_path) or self.is_generated_code(file_path):
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
        """Scan target path using parallel ThreadPoolExecutor for high performance."""
        target = Path(target_path).resolve()
        if not target.exists():
            raise FileNotFoundError(f"Target path does not exist: {target}")

        self.seen_realpaths.clear()
        scanned_files: List[ScannedFile] = []
        root = target if target.is_dir() else target.parent

        if target.is_file():
            sf = self.scan_file(target, root)
            if sf:
                scanned_files.append(sf)
        else:
            file_candidates: List[Path] = []
            for current_root, dirs, files in os.walk(target, followlinks=False):
                dirs[:] = [
                    d for d in dirs
                    if d not in self.ignored_folders and not d.startswith(".")
                ]
                for file in files:
                    file_candidates.append(Path(current_root) / file)

            # Parallel scanning using ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=min(16, os.cpu_count() or 4)) as executor:
                futures = [executor.submit(self.scan_file, f, root) for f in file_candidates]
                for future in as_completed(futures):
                    res = future.result()
                    if res:
                        scanned_files.append(res)

        # Sort files by relative path for deterministic results
        scanned_files.sort(key=lambda x: x.relative_path)

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
