from pathlib import Path
from app.ai.ollama_provider import OllamaProvider
from app.history import HistoryManager


def test_ollama_provider_init_and_parsing():
    provider = OllamaProvider(model="deepseek-coder:6.7b", ollama_host="http://localhost:11434")
    assert provider.model == "deepseek-coder:6.7b"
    assert provider.provider_name == "Ollama (Local LLM)"

    raw_response = '{"issues": [{"severity": "HIGH", "category": "Security", "title": "Command Injection", "description": "Unsafe os.system call", "suggestion": "Use subprocess.run"}], "summary": "Review complete"}'
    parsed = provider._parse_json_response(raw_response, "main.py")
    assert len(parsed.issues) == 1
    assert parsed.issues[0].title == "Command Injection"
    assert parsed.issues[0].severity == "HIGH"


def test_history_manager_sqlite(tmp_path: Path):
    db_file = tmp_path / "test_history.db"
    manager = HistoryManager(db_path=db_file)

    rec_id = manager.record_review(
        target_path="/src/app",
        overall_score=8.7,
        security_score=10.0,
        maintainability_score=8.4,
        quality_score=9.3,
        performance_score=9.2,
        doc_score=5.0,
        test_score=8.5,
        total_files=25,
        total_issues=2,
        high_issues=0,
        technical_debt_hours=0.9,
        branch="main",
        commit_hash="abc1234",
    )

    assert rec_id > 0

    history = manager.get_history(limit=5)
    assert len(history) == 1
    assert history[0].overall_score == 8.7
    assert history[0].security_score == 10.0
    assert history[0].total_files == 25
    assert history[0].commit_hash == "abc1234"
