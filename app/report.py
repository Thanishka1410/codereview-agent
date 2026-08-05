import json
from pathlib import Path
from typing import Optional, List, Dict
from jinja2 import Template
from app.reviewer import ProjectReviewResult
from app.templates import HTML_REPORT_TEMPLATE


def generate_json_report(result: ProjectReviewResult) -> str:
    """Generate machine-readable JSON report string."""
    return result.model_dump_json(indent=2)


def generate_markdown_report(result: ProjectReviewResult) -> str:
    """Generate Markdown report string."""
    md = []
    md.append("# 🤖 CodeReview Agent - Professional Review Report\n")
    md.append(f"**Root Directory:** `{result.scan_result.root_path}`  ")
    md.append(f"**AI Engine:** {result.provider_name} ({result.model_name})  ")
    md.append(f"**Files Reviewed:** {result.scan_result.total_files} | **Total Lines:** {result.scan_result.total_lines:,}  \n")

    md.append("## 📊 Weighted Quality Scores\n")
    md.append(f"- **Overall Health Score:** `{result.scores.overall_score} / 10.0`")
    md.append(f"- **Security Score (40%):** `{result.scores.security_score} / 10.0`")
    md.append(f"- **Code Quality Score (25%):** `{result.scores.code_quality_score} / 10.0`")
    md.append(f"- **Maintainability Score (25%):** `{result.scores.maintainability_score} / 10.0`")
    md.append(f"- **Performance Score (15%):** `{result.scores.performance_score} / 10.0`")
    md.append(f"- **Estimated Technical Debt:** `{result.scores.estimated_technical_debt_hours} Hours`\n")

    md.append(f"## 🐛 Findings Overview ({len(result.issues)})\n")
    if not result.issues:
        md.append("✓ No code issues detected across codebase.\n")
    else:
        for idx, issue in enumerate(result.issues, start=1):
            line_str = f" Line {issue.line_number}" if issue.line_number else ""
            md.append(f"### {idx}. [{issue.severity}] `{issue.file_path}`{line_str}")
            md.append(f"**Category:** {issue.category} | **Fix Time:** ~{issue.estimated_fix_minutes}m | **Confidence:** {issue.confidence_score*100:.0f}%  ")
            md.append(f"**Issue:** {issue.title}  ")
            md.append(f"**Description:** {issue.description}  ")
            md.append(f"**Suggestion:** {issue.suggestion}  ")
            if issue.code_example:
                md.append(f"```\n{issue.code_example}\n```")
            md.append("\n---\n")

    return "\n".join(md)


def generate_html_report(result: ProjectReviewResult) -> str:
    """Generate single-file Chart.js HTML report."""
    template = Template(HTML_REPORT_TEMPLATE)
    return template.render(result=result)


def export_reports(
    result: ProjectReviewResult,
    output_dir: str = "reports",
    formats: Optional[List[str]] = None,
) -> Dict[str, Path]:
    """Export reports to specified output folder."""
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    target_formats = formats or ["json", "markdown", "html"]
    saved_files = {}

    if "json" in target_formats:
        json_file = out_path / "codereview_report.json"
        json_file.write_text(generate_json_report(result), encoding="utf-8")
        saved_files["json"] = json_file

    if "markdown" in target_formats or "md" in target_formats:
        md_file = out_path / "codereview_report.md"
        md_file.write_text(generate_markdown_report(result), encoding="utf-8")
        saved_files["markdown"] = md_file

    if "html" in target_formats:
        html_file = out_path / "codereview_report.html"
        html_file.write_text(generate_html_report(result), encoding="utf-8")
        saved_files["html"] = html_file

    return saved_files
