from pathlib import Path
from app.cache import FileCacheManager
from app.ai.base import ReviewIssue

def test_file_cache(tmp_path):
    cache_file = tmp_path / "test_cache.json"
    manager = FileCacheManager(cache_file=cache_file)
    
    sample_file = tmp_path / "test.py"
    sample_file.write_text("print('hello')", encoding="utf-8")
    
    issues = [
        ReviewIssue(
            severity="LOW",
            category="Quality",
            file_path="test.py",
            title="Test Issue",
            description="Test desc",
            suggestion="Test sug"
        )
    ]
    
    manager.update_cache(sample_file, "test.py", issues)
    manager.save_cache()
    
    assert manager.is_file_unchanged(sample_file, "test.py") is True
    cached_issues = manager.get_cached_issues("test.py")
    assert len(cached_issues) == 1
