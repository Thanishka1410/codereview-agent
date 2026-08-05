import json
from pathlib import Path
from typing import Optional
from jinja2 import Template
from app.reviewer import ProjectReviewResult


HTML_REPORT_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CodeReview Agent Report</title>
    <style>
        :root {
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --text-color: #f8fafc;
            --accent-color: #38bdf8;
            --high-color: #ef4444;
            --med-color: #f59e0b;
            --low-color: #3b82f6;
            --info-color: #64748b;
        }
        body {
            font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            margin: 0;
            padding: 2rem;
            line-height: 1.6;
        }
        .container {
            max-width: 1100px;
            margin: 0 auto;
        }
        .header {
            border-bottom: 2px solid #334155;
            padding-bottom: 1rem;
            margin-bottom: 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .score-card {
            background: linear-gradient(135deg, #1e1b4b, #312e81);
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
            margin-bottom: 2rem;
            border: 1px solid #4338ca;
        }
        .score-number {
            font-size: 3.5rem;
            font-weight: 800;
            color: #38bdf8;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }
        .card {
            background: var(--card-bg);
            border-radius: 8px;
            padding: 1.2rem;
            border: 1px solid #334155;
        }
        .issue-card {
            background: var(--card-bg);
            border-radius: 8px;
            padding: 1.2rem;
            margin-bottom: 1rem;
            border-left: 5px solid var(--info-color);
        }
        .issue-card.HIGH { border-left-color: var(--high-color); }
        .issue-card.MEDIUM { border-left-color: var(--med-color); }
        .issue-card.LOW { border-left-color: var(--low-color); }
        .badge {
            display: inline-block;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: bold;
            color: white;
        }
        .badge.HIGH { background-color: var(--high-color); }
        .badge.MEDIUM { background-color: var(--med-color); }
        .badge.LOW { background-color: var(--low-color); }
        .badge.INFO { background-color: var(--info-color); }
        code {
            background-color: #0f172a;
            padding: 0.2rem 0.4rem;
            border-radius: 4px;
            font-family: monospace;
        }
        pre {
            background-color: #0f172a;
            padding: 1rem;
            border-radius: 6px;
            overflow-x: auto;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1>CodeReview Agent Report</h1>
                <p style="color: #94a3b8;">Scanned {{ result.scan_result.total_files }} files | AI Provider: {{ result.provider_name }} ({{ result.model_name }})</p>
            </div>
        </div>

        <div class="score-card">
            <h2>Overall Health Score</h2>
            <div class="score-number">{{ result.scores.overall_score }} / 10.0</div>
            <p>Target Threshold: 8.5 / 10.0</p>
        </div>

        <div class="grid">
            <div class="card">
                <h3>Security Score</h3>
                <p class="score-number" style="font-size: 2rem;">{{ result.scores.security_score }}</p>
            </div>
            <div class="card">
                <h3>Maintainability</h3>
                <p class="score-number" style="font-size: 2rem;">{{ result.scores.maintainability_score }}</p>
            </div>
            <div class="card">
                <h3>Code Quality</h3>
                <p class="score-number" style="font-size: 2rem;">{{ result.scores.code_quality_score }}</p>
            </div>
            <div class="card">
                <h3>Est. Tech Debt</h3>
                <p class="score-number" style="font-size: 2rem;">{{ result.scores.estimated_technical_debt_hours }}h</p>
            </div>
        </div>

        <h2>Identified Issues ({{ result.issues | length }})</h2>
        {% for issue in result.issues %}
        <div class="issue-card {{ issue.severity }}">
            <div>
                <span class="badge {{ issue.severity }}">{{ issue.severity }}</span>
                <strong>{{ issue.file_path }}</strong> {% if issue.line_number %}(Line {{ issue.line_number }}){% endif %}
                <span style="float: right; color: #94a3b8;">{{ issue.category }}</span>
            </div>
            <h3>{{ issue.title }}</h3>
            <p>{{ issue.description }}</p>
            <div style="margin-top: 0.5rem;">
                <strong>Suggestion:</strong>
                <pre><code>{{ issue.suggestion }}</code></pre>
            </div>
        </div>
        {% endfor %}
    </div>
</body>
</html>
"""


def generate_json_report(result: ProjectReviewResult) -> str:
    """Generate JSON report string."""
    return result.model_dump_json(indent=2)


def generate_markdown_report(result: ProjectReviewResult) -> str:
    """Generate Markdown report string."""
    md = []
    md.append("# CodeReview Agent - Review Report\n")
    md.append(f"**AI Provider:** {result.provider_name} ({result.model_name})  ")
    md.append(f"**Files Reviewed:** {result.scan_result.total_files} | **Total Lines:** {result.scan_result.total_lines:,}  \n")

    md.append("## Project Health Scores\n")
    md.append(f"- **Overall Health Score:** {result.scores.overall_score} / 10.0")
    md.append(f"- **Security Score:** {result.scores.security_score} / 10.0")
    md.append(f"- **Code Quality Score:** {result.scores.code_quality_score} / 10.0")
    md.append(f"- **Maintainability Score:** {result.scores.maintainability_score} / 10.0")
    md.append(f"- **Performance Score:** {result.scores.performance_score} / 10.0")
    md.append(f"- **Estimated Technical Debt:** {result.scores.estimated_technical_debt_hours} Hours")
    md.append(f"- **Average Cyclomatic Complexity:** {result.scores.average_cyclomatic_complexity}\n")

    md.append(f"## Code Review Findings ({len(result.issues)})\n")
    if not result.issues:
        md.append("No code issues detected.\n")
    else:
        for idx, issue in enumerate(result.issues, start=1):
            line_str = f" Line {issue.line_number}" if issue.line_number else ""
            md.append(f"### {idx}. [{issue.severity}] `{issue.file_path}`{line_str}")
            md.append(f"**Category:** {issue.category}  ")
            md.append(f"**Issue:** {issue.title}  ")
            md.append(f"**Description:** {issue.description}  ")
            md.append(f"**Suggestion:**\n```\n{issue.suggestion}\n```\n")

    return "\n".join(md)


def generate_html_report(result: ProjectReviewResult) -> str:
    """Generate HTML report string using Jinja2 template."""
    template = Template(HTML_REPORT_TEMPLATE)
    return template.render(result=result)


def export_reports(
    result: ProjectReviewResult,
    output_dir: str = "reports",
    formats: Optional[list[str]] = None,
) -> dict[str, Path]:
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
