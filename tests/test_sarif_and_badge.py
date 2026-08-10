import json
from pathlib import Path
from app.ai.base import ReviewIssue
from app.sarif import SARIFGenerator
from app.badge import BadgeGenerator


def test_sarif_generator_valid_schema(tmp_path: Path):
    issues = [
        ReviewIssue(
            severity="HIGH",
            file_path="app/main.py",
            line_number=42,
            category="Security",
            title="SQL Injection Vulnerability",
            description="Raw string concatenation detected in SQL query.",
            suggestion="Use parameterized placeholders.",
        ),
        ReviewIssue(
            severity="MEDIUM",
            file_path="app/utils.py",
            line_number=10,
            category="Quality",
            title="Deep Nesting",
            description="Deeply nested conditionals.",
            suggestion="Use guard clauses.",
        ),
    ]

    generator = SARIFGenerator(issues, target_path=str(tmp_path))
    sarif_dict = generator.generate_sarif_dict()

    assert sarif_dict["version"] == "2.1.0"
    assert "runs" in sarif_dict
    assert len(sarif_dict["runs"]) == 1

    driver = sarif_dict["runs"][0]["tool"]["driver"]
    assert driver["name"] == "CodeReview-Agent"
    assert len(driver["rules"]) == 2

    results = sarif_dict["runs"][0]["results"]
    assert len(results) == 2
    assert results[0]["level"] == "error"
    assert results[0]["locations"][0]["physicalLocation"]["artifactLocation"]["uri"] == "app/main.py"
    assert results[1]["level"] == "warning"

    output_file = tmp_path / "test.sarif"
    generator.export_sarif_file(output_file)
    assert output_file.is_file()

    loaded = json.loads(output_file.read_text(encoding="utf-8"))
    assert loaded["version"] == "2.1.0"


def test_badge_generator_colors_and_svg(tmp_path: Path):
    assert BadgeGenerator.get_color_for_score(9.1) == "#4c1"
    assert BadgeGenerator.get_color_for_score(8.0) == "#a4a61d"
    assert BadgeGenerator.get_color_for_score(6.5) == "#fe7d37"
    assert BadgeGenerator.get_color_for_score(4.5) == "#e05d44"

    svg_content = BadgeGenerator.generate_svg(9.1, label="code health")
    assert "<svg" in svg_content
    assert "9.1 / 10" in svg_content
    assert "#4c1" in svg_content

    badge_file = tmp_path / "badge.svg"
    BadgeGenerator.export_badge_file(9.1, badge_file)
    assert badge_file.is_file()
    assert "<svg" in badge_file.read_text(encoding="utf-8")
