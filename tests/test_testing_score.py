from pathlib import Path
from app.config import ReviewConfig
from app.scanner import Scanner
from app.reviewer import ReviewerEngine


def test_testing_score_calculation(tmp_path: Path):
    """Verify that projects with zero tests score low (1.0) and projects with test files score higher."""
    # 1. Project with NO test files
    untested_dir = tmp_path / "untested_proj"
    untested_dir.mkdir()
    (untested_dir / "app.py").write_text("def run():\n    print('running')", encoding="utf-8")
    (untested_dir / "utils.py").write_text("def helper():\n    return 42", encoding="utf-8")

    config = ReviewConfig(provider="mock")
    engine = ReviewerEngine(config)
    untested_result = engine.run_review(untested_dir)

    assert untested_result.scan_result.test_files_count == 0
    assert untested_result.scores.testing_score == 1.0

    # 2. Project WITH test files
    tested_dir = tmp_path / "tested_proj"
    tested_dir.mkdir()
    (tested_dir / "app.py").write_text("def run():\n    print('running')", encoding="utf-8")
    (tested_dir / "test_app.py").write_text("def test_run():\n    assert True", encoding="utf-8")

    tested_result = engine.run_review(tested_dir)

    assert tested_result.scan_result.test_files_count == 1
    assert tested_result.scores.testing_score > 1.0
    assert tested_result.scores.testing_score >= 5.0
