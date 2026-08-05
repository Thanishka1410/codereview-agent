from app.github import GitHubIntegrationEngine, format_github_actions_annotation
from app.ai.base import ReviewIssue

def test_github_actions_annotation():
    issue = ReviewIssue(
        severity="HIGH",
        category="Security",
        file_path="app/auth.py",
        line_number=45,
        title="SQL Injection Vulnerability",
        description="Unsafe query format",
        suggestion="Use parameterized query"
    )
    annotation = format_github_actions_annotation(issue)
    assert annotation.startswith("::error file=app/auth.py,line=45,title=SQL Injection Vulnerability::Unsafe query format")

def test_github_pr_payload():
    engine = GitHubIntegrationEngine()
    issue = ReviewIssue(
        severity="HIGH",
        category="Security",
        file_path="app/auth.py",
        line_number=45,
        title="SQL Injection Vulnerability",
        description="Unsafe query format",
        suggestion="Use parameterized query"
    )
    payload = engine.create_pr_review_payload(pr_number=101, issues=[issue], overall_score=5.5)
    assert payload.event == "REQUEST_CHANGES"
    assert len(payload.comments) == 1
