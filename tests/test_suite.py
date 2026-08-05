import os
from pathlib import Path
import pytest
from app.config import ReviewConfig, load_config
from app.scanner import Scanner
from app.utils import analyze_file_structure, get_git_info
from app.ai.factory import get_ai_provider
from app.reviewer import ReviewerEngine

TEST_DIR = Path(__file__).parent.parent / "examples" / "sample_project"

def test_load_config():
    config = load_config()
    assert isinstance(config, ReviewConfig)
    assert config.provider in ["mock", "openai", "gemini", "claude"]

def test_scanner():
    scanner = Scanner()
    res = scanner.scan(TEST_DIR)
    assert res.total_files >= 2
    assert "python" in res.language_breakdown or "javascript" in res.language_breakdown

def test_utils_ast_analysis():
    sample_py = TEST_DIR / "sample_vulnerable.py"
    metrics = analyze_file_structure(sample_py, "sample_vulnerable.py", "python")
    assert metrics.language == "python"
    assert "get_user_data" in metrics.functions
    assert "execute_user_code" in metrics.functions
    assert metrics.complexity > 1

def test_ai_mock_provider():
    config = ReviewConfig(provider="mock")
    provider = get_ai_provider(config)
    sample_py = TEST_DIR / "sample_vulnerable.py"
    metrics = analyze_file_structure(sample_py, "sample_vulnerable.py", "python")
    
    resp = provider.review_code(
        file_path="sample_vulnerable.py",
        code=metrics.code_content,
        language="python",
        functions=metrics.functions,
    )
    assert len(resp.issues) > 0
    # Expect SQL injection & Secret detection in mock provider
    severities = [i.severity for i in resp.issues]
    assert "HIGH" in severities

def test_reviewer_engine():
    config = ReviewConfig(provider="mock")
    engine = ReviewerEngine(config)
    result = engine.run_review(TEST_DIR)
    
    assert result.scan_result.total_files >= 2
    assert len(result.issues) > 0
    assert result.scores.overall_score >= 0.0 and result.scores.overall_score <= 10.0
