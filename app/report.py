import json
from pathlib import Path
from typing import Optional, List, Dict
from jinja2 import Template
from app.reviewer import ProjectReviewResult


HTML_REPORT_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CodeReview Agent - Production Quality Dashboard</title>
    <!-- Chart.js CDN -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --text-color: #f8fafc;
            --subtext-color: #94a3b8;
            --accent-color: #38bdf8;
            --high-color: #ef4444;
            --med-color: #f59e0b;
            --low-color: #3b82f6;
            --info-color: #64748b;
            --border-color: #334155;
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
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            border-bottom: 2px solid var(--border-color);
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
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
        }
        .score-number {
            font-size: 3.5rem;
            font-weight: 800;
            color: #38bdf8;
        }
        .charts-row {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        .chart-card {
            background: var(--card-bg);
            border-radius: 10px;
            padding: 1.2rem;
            border: 1px solid var(--border-color);
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }
        .card {
            background: var(--card-bg);
            border-radius: 8px;
            padding: 1.2rem;
            border: 1px solid var(--border-color);
            text-align: center;
        }
        .filter-bar {
            margin-bottom: 1.5rem;
            display: flex;
            gap: 0.5rem;
        }
        .btn-filter {
            background: #334155;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
        }
        .btn-filter.active {
            background: var(--accent-color);
            color: #0f172a;
        }
        .issue-card {
            background: var(--card-bg);
            border-radius: 8px;
            padding: 1.2rem;
            margin-bottom: 1rem;
            border-left: 5px solid var(--info-color);
            border-top: 1px solid var(--border-color);
            border-right: 1px solid var(--border-color);
            border-bottom: 1px solid var(--border-color);
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
        pre {
            background-color: #0f172a;
            padding: 1rem;
            border-radius: 6px;
            overflow-x: auto;
            border: 1px solid var(--border-color);
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }
        th, td {
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }
        th { background-color: #1e293b; color: var(--accent-color); }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1>🤖 CodeReview Agent Dashboard</h1>
                <p style="color: var(--subtext-color);">
                    Root: <code>{{ result.scan_result.root_path }}</code> | 
                    Files: <strong>{{ result.scan_result.total_files }}</strong> | 
                    LOC: <strong>{{ "{:,}".format(result.scan_result.total_lines) }}</strong>
                </p>
            </div>
            <div>
                <span class="badge INFO" style="font-size: 1rem; padding: 0.5rem 1rem;">
                    AI Engine: {{ result.provider_name }} ({{ result.model_name }})
                </span>
            </div>
        </div>

        <div class="score-card">
            <h2>Overall Quality & Health Score</h2>
            <div class="score-number">{{ result.scores.overall_score }} / 10.0</div>
            <p>Target Threshold: 8.5 / 10.0</p>
        </div>

        <!-- Chart.js Visualization Section -->
        <div class="charts-row">
            <div class="chart-card">
                <h3>Issue Severity Distribution</h3>
                <canvas id="severityChart"></canvas>
            </div>
            <div class="chart-card">
                <h3>Quality Sub-Scores (0-10)</h3>
                <canvas id="scoresChart"></canvas>
            </div>
        </div>

        <div class="grid">
            <div class="card">
                <h3>Security</h3>
                <p class="score-number" style="font-size: 2.2rem;">{{ result.scores.security_score }}</p>
            </div>
            <div class="card">
                <h3>Maintainability</h3>
                <p class="score-number" style="font-size: 2.2rem;">{{ result.scores.maintainability_score }}</p>
            </div>
            <div class="card">
                <h3>Code Quality</h3>
                <p class="score-number" style="font-size: 2.2rem;">{{ result.scores.code_quality_score }}</p>
            </div>
            <div class="card">
                <h3>Est. Tech Debt</h3>
                <p class="score-number" style="font-size: 2.2rem;">{{ result.scores.estimated_technical_debt_hours }}h</p>
            </div>
        </div>

        <!-- Issue Interactive List -->
        <h2>Identified Issues ({{ result.issues | length }})</h2>
        <div class="filter-bar">
            <button class="btn-filter active" onclick="filterIssues('ALL')">All ({{ result.issues | length }})</button>
            <button class="btn-filter" onclick="filterIssues('HIGH')">High ({{ result.high_severity_count }})</button>
            <button class="btn-filter" onclick="filterIssues('MEDIUM')">Medium ({{ result.medium_severity_count }})</button>
            <button class="btn-filter" onclick="filterIssues('LOW')">Low ({{ result.low_severity_count }})</button>
            <button class="btn-filter" onclick="filterIssues('INFO')">Info ({{ result.info_severity_count }})</button>
        </div>

        {% for issue in result.issues %}
        <div class="issue-card {{ issue.severity }}">
            <div>
                <span class="badge {{ issue.severity }}">{{ issue.severity }}</span>
                <strong>{{ issue.file_path }}</strong> {% if issue.line_number %}(Line {{ issue.line_number }}){% endif %}
                <span style="float: right; color: var(--subtext-color);">Category: {{ issue.category }} | Fix Time: ~{{ issue.estimated_fix_minutes }}m</span>
            </div>
            <h3 style="margin-top: 0.5rem;">{{ issue.title }}</h3>
            <p>{{ issue.description }}</p>
            <div>
                <strong>Actionable Fix:</strong> {{ issue.suggestion }}
            </div>
            {% if issue.code_example %}
            <pre><code>{{ issue.code_example }}</code></pre>
            {% endif %}
        </div>
        {% endfor %}
    </div>

    <script>
        // Render Chart.js Charts
        const severityCtx = document.getElementById('severityChart').getContext('2d');
        new Chart(severityCtx, {
            type: 'doughnut',
            data: {
                labels: ['High', 'Medium', 'Low', 'Info'],
                datasets: [{
                    data: [
                        {{ result.high_severity_count }},
                        {{ result.medium_severity_count }},
                        {{ result.low_severity_count }},
                        {{ result.info_severity_count }}
                    ],
                    backgroundColor: ['#ef4444', '#f59e0b', '#3b82f6', '#64748b']
                }]
            },
            options: { plugins: { legend: { labels: { color: '#f8fafc' } } } }
        });

        const scoresCtx = document.getElementById('scoresChart').getContext('2d');
        new Chart(scoresCtx, {
            type: 'bar',
            data: {
                labels: ['Security', 'Quality', 'Maintainability', 'Performance'],
                datasets: [{
                    label: 'Sub-Score',
                    data: [
                        {{ result.scores.security_score }},
                        {{ result.scores.code_quality_score }},
                        {{ result.scores.maintainability_score }},
                        {{ result.scores.performance_score }}
                    ],
                    backgroundColor: '#38bdf8'
                }]
            },
            options: {
                scales: {
                    y: { beginAtZero: true, max: 10, ticks: { color: '#f8fafc' } },
                    x: { ticks: { color: '#f8fafc' } }
                },
                plugins: { legend: { display: false } }
            }
        });

        function filterIssues(severity) {
            const cards = document.querySelectorAll('.issue-card');
            cards.forEach(card => {
                if (severity === 'ALL' || card.classList.contains(severity)) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
            document.querySelectorAll('.btn-filter').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
        }
    </script>
</body>
</html>
"""


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
