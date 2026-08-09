from pathlib import Path
from app.hooks import GitHookManager


def test_git_hook_manager_install_and_uninstall(tmp_path: Path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()

    manager = GitHookManager(root_path=tmp_path)
    hook_file = manager.install_pre_commit_hook()

    assert hook_file.is_file()
    assert "codereview" in hook_file.read_text(encoding="utf-8")

    uninstalled = manager.uninstall_pre_commit_hook()
    assert uninstalled is True
    assert not hook_file.exists()
