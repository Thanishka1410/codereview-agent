"""
Automated Git pre-commit hook installation and management utility for CodeReview Agent.
"""

import os
import stat
from pathlib import Path
from typing import Optional
from rich.console import Console

console = Console()

PRE_COMMIT_SCRIPT_TEMPLATE = """#!/bin/sh
# CodeReview Agent - Pre-Commit Hook
# Automatically runs static & AI code review on staged changes prior to commit.

echo "🔍 Running CodeReview Agent on staged git files..."

codereview review . --diff --quiet
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo "❌ CodeReview failed! Please resolve high-severity issues or raise project score before committing."
    exit $EXIT_CODE
fi

echo "✅ CodeReview passed successfully!"
exit 0
"""


class GitHookManager:
    """Manages installation and uninstallation of Git pre-commit hooks."""

    def __init__(self, root_path: Optional[Path] = None):
        self.root_path = Path(root_path or Path.cwd()).resolve()

    def find_git_dir(self) -> Optional[Path]:
        """Locate root .git directory."""
        current = self.root_path
        while current != current.parent:
            git_dir = current / ".git"
            if git_dir.is_dir():
                return git_dir
            current = current.parent
        return None

    def install_pre_commit_hook(self) -> Path:
        """Install executable pre-commit hook script inside .git/hooks/."""
        git_dir = self.find_git_dir()
        if not git_dir:
            raise FileNotFoundError(f"No .git repository directory found at or above '{self.root_path}'.")

        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir(exist_ok=True)

        hook_file = hooks_dir / "pre-commit"
        hook_file.write_text(PRE_COMMIT_SCRIPT_TEMPLATE, encoding="utf-8")

        # Set executable permissions (chmod +x)
        try:
            current_mode = os.stat(hook_file).st_mode
            os.chmod(hook_file, current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        except OSError:
            pass

        return hook_file

    def uninstall_pre_commit_hook(self) -> bool:
        """Remove pre-commit hook script from .git/hooks/."""
        git_dir = self.find_git_dir()
        if not git_dir:
            return False

        hook_file = git_dir / "hooks" / "pre-commit"
        if hook_file.is_file():
            hook_file.unlink()
            return True
        return False
