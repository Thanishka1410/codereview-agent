from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from app.reviewer import ProjectReviewResult, HealthScores
from app.ai.base import ReviewIssue

console = Console()


def print_banner(quiet: bool = False):
    """Print ASCII Art Header Banner for CodeReview Agent unless in quiet mode."""
    if quiet:
        return
    banner_text = """[bold cyan]
  ____ ___  ____  _____ ____  _____  __   __ _____ _____ _        __
 / ___/ _ \|  _ \| ____|  _ \| ____| \ \ / / |_ _| ____| \      / /
| |  | | | | | | |  _| | |_) |  _|    \ V /   | ||  _|  \ \    / / 
| |__| |_| | |_| | |___|  _ <| |___    \ /    | || |___  \ \/\/ /  
 \____\___/|____/|_____|_| \_\_____|    V    |___|_____|  \_/\_/   
[/bold cyan][dim]                 AI-Powered Production Code Review CLI Agent v1.1.0[/dim]
"""
    console.print(banner_text)


def print_scan_summary(scan_result, quiet: bool = False):
    """Display project scan summary table."""
    if quiet:
        return
    table = Table(title="Project Scan Summary", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="bold green")

    table.add_row("Root Directory", str(scan_result.root_path))
    table.add_row("Files Found", str(scan_result.total_files))
    table.add_row("Total Lines of Code", f"{scan_result.total_lines:,}")
    table.add_row("Total Size", f"{scan_result.total_size_bytes / 1024:.1f} KB")
    table.add_row("Primary Language", scan_result.primary_language.upper())

    console.print(table)


def print_issues(issues: list[ReviewIssue], quiet: bool = False, verbose: bool = False):
    """Print formatted code review issues grouped by severity."""
    if quiet:
        return
    if not issues:
        console.print("\n[bold green]✓ No code issues found! Codebase looks clean.[/bold green]\n")
        return

    console.print(f"\n[bold yellow]Found {len(issues)} code review finding(s):[/bold yellow]\n")

    severity_styles = {
        "HIGH": "bold white on red",
        "MEDIUM": "bold black on yellow",
        "LOW": "bold white on blue",
        "INFO": "dim white on black",
    }

    for issue in issues:
        style = severity_styles.get(issue.severity.upper(), "bold white")
        badge = f"[{style}] {issue.severity.upper()} [/{style}]"
        line_str = f" line {issue.line_number}" if issue.line_number else ""

        title_text = f"{badge} [bold white]{issue.file_path}{line_str}[/bold white] - [cyan]{issue.title}[/cyan]"

        fix_info = f"\n[dim]Estimated Fix Time: ~{issue.estimated_fix_minutes}m | Confidence: {issue.confidence_score*100:.0f}%[/dim]"
        code_ex = f"\n\n[bold green]Suggested Code Example:[/bold green]\n[dim]{issue.code_example}[/dim]" if issue.code_example else ""

        body_content = (
            f"[bold]Category:[/bold] {issue.category}\n"
            f"[bold]Problem:[/bold] {issue.description}\n\n"
            f"[bold green]Actionable Suggestion:[/bold green]\n{issue.suggestion}"
            f"{code_ex}{fix_info}"
        )

        panel = Panel(
            body_content,
            title=title_text,
            subtitle=f"[dim]CodeReview AI Finding[/dim]",
            border_style="red" if issue.severity == "HIGH" else ("yellow" if issue.severity == "MEDIUM" else "blue"),
            expand=False,
        )
        console.print(panel)


def print_scores(scores: HealthScores, quiet: bool = False):
    """Display overall health score card and sub-metrics."""
    if quiet:
        return
    overall = scores.overall_score
    color = "bold green" if overall >= 8.0 else ("bold yellow" if overall >= 6.0 else "bold red")

    score_panel = Panel(
        f"[{color}][size=20]Weighted Overall Health Score: {overall} / 10.0[/size][/{color}]\n"
        f"[dim]Target Threshold: 8.5 / 10.0[/dim]",
        title="[bold yellow]Project Quality & Security Assessment[/bold yellow]",
        border_style="magenta",
        expand=False,
    )
    console.print("\n", score_panel)

    table = Table(title="Sub-Scores & Weighted Metrics", show_header=True, header_style="bold blue")
    table.add_column("Category", style="cyan")
    table.add_column("Score / Metric", style="bold white")

    table.add_row("Security Score (40%)", f"{scores.security_score} / 10.0")
    table.add_row("Maintainability Score (25%)", f"{scores.maintainability_score} / 10.0")
    table.add_row("Code Quality Score (15%)", f"{scores.code_quality_score} / 10.0")
    table.add_row("Performance Score (10%)", f"{scores.performance_score} / 10.0")
    table.add_row("Documentation Score (5%)", f"{scores.documentation_score} / 10.0")
    table.add_row("Avg Cyclomatic Complexity", f"{scores.average_cyclomatic_complexity}")
    table.add_row("Est. Technical Debt", f"{scores.estimated_technical_debt_hours} Hours")

    console.print(table)


def print_review_complete_summary(result: ProjectReviewResult, quiet: bool = False):
    """Print clean terminal completion block."""
    if quiet:
        console.print(f"Score: {result.scores.overall_score}/10.0 | Issues: {len(result.issues)} (HIGH: {result.high_severity_count})")
        return
    color = "green" if result.high_severity_count == 0 else "red"
    summary_text = (
        f"[{color}]Review Completed![/{color}]\n"
        f"Files Reviewed: [bold]{result.scan_result.total_files}[/bold] | "
        f"Issues Found: [bold]{len(result.issues)}[/bold] ("
        f"[red]HIGH: {result.high_severity_count}[/red], "
        f"[yellow]MED: {result.medium_severity_count}[/yellow], "
        f"[blue]LOW: {result.low_severity_count}[/blue]) | "
        f"Score: [bold]{result.scores.overall_score}/10.0[/bold]"
    )
    console.print(Panel(summary_text, border_style=color, title="CodeReview Agent Status"))
