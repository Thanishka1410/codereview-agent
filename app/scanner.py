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
    is_test_file: bool = False


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
    test_files_count: int = 0
    test_lines_count: int = 0


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
                "__pycache__", ".pytest_cache", ".egg-info", ".idea", ".vscode", "reports", "examples"
            ]
        )
        self.ignored_files: Set[str] = set(
            ignored_files
            or ["package-lock.json", "yarn.lock", "poetry.lock", "Pipfile.lock", ".codereview_cache.json", ".codereview_history.db"]
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
        except (OSError, UnicodeDecodeError):
            return False
        return False

    def detect_language(self, file_path: Path) -> str:
        """Detect programming language based on file extension."""
        ext = file_path.suffix.lower()
        return EXTENSION_TO_LANGUAGE.get(ext, "unknown")

    def is_test_file(self, file_path: Path, relative_path: str) -> bool:
        """Determine if a file is a unit/integration test file based on directory or naming convention."""
        norm_path = relative_path.replace("\\", "/").lower()
        file_name = file_path.name.lower()
        path_parts = [p.lower() for p in Path(norm_path).parts]

        # Directory conventions: tests/, test/, __tests__/, spec/, specs/
        test_dirs = {"tests", "test", "__tests__", "spec", "specs"}
        if any(part in test_dirs for part in path_parts[:-1]):
            return True

        # Filename conventions across languages
        test_patterns = [
            "test_*.py", "*_test.py",
            "*.test.js", "*.spec.js", "*.test.jsx", "*.spec.jsx",
            "*.test.ts", "*.spec.ts", "*.test.tsx", "*.spec.tsx",
            "*test.java", "*tests.java", "*test.kt", "*tests.kt", "*spec.kt",
            "*_test.go", "*test.cs", "*test.php", "*tests.swift", "*test.dart",
            "test_*.rb", "*_spec.rb",
        ]
        return any(fnmatch.fnmatch(file_name, pat) for pat in test_patterns)

    def should_ignore(self, path: Path, root: Path) -> bool:
        """Check if file/folder should be ignored."""
        name = path.name

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

        if self.exclude_patterns:
            if any(fnmatch.fnmatch(name, pat) for pat in self.exclude_patterns):
                return True

        if self.include_patterns:
            if not any(fnmatch.fnmatch(name, pat) for pat in self.include_patterns):
                return True

        return False

    def scan_file(self, file_path: Path, root: Path) -> Optional[ScannedFile]:
        """Scan a single file and collect metadata."""
        if not file_path.is_file():
            return None

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
        is_test = self.is_test_file(file_path, rel_path)

        return ScannedFile(
            path=file_path.resolve(),
            relative_path=rel_path,
            extension=file_path.suffix.lower(),
            language=language,
            size_bytes=size_bytes,
            line_count=line_count,
            is_test_file=is_test,
        )

    def _collect_file_candidates(self, target: Path) -> List[Path]:
        """Collect all candidate file paths for parallel scanning."""
        file_candidates: List[Path] = []
        for current_root, dirs, files in os.walk(target, followlinks=False):
            dirs[:] = [
                d for d in dirs
                if d not in self.ignored_folders and not d.startswith(".")
            ]
            for file in files:
                file_candidates.append(Path(current_root) / file)
        return file_candidates

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
            file_candidates = self._collect_file_candidates(target)

            workers = min(16, os.cpu_count() or 4)
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = [executor.submit(self.scan_file, f, root) for f in file_candidates]
                for future in as_completed(futures):
                    res = future.result()
                    if res:
                        scanned_files.append(res)

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

        test_files_count = sum(1 for f in scanned_files if f.is_test_file)
        test_lines_count = sum(f.line_count for f in scanned_files if f.is_test_file)

        return ProjectScanResult(
            root_path=root,
            files=scanned_files,
            total_files=total_files,
            total_lines=total_lines,
            total_size_bytes=total_size_bytes,
            primary_language=primary_lang,
            language_breakdown=lang_counts,
            test_files_count=test_files_count,
            test_lines_count=test_lines_count,
        )
