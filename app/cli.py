import sys
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from app import __version__
from app.config import load_config, ReviewConfig
from app.reviewer import ReviewerEngine, ProjectReviewResult
from app.formatter import (
    print_banner,
    print_scan_summary,
    print_issues,
    print_scores,
    print_review_complete_summary,
)
from app.report import (
    generate_json_report,
    generate_markdown_report,
    generate_html_report,
    export_reports,
)
from app.github import format_github_actions_annotation

app = typer.Typer(
    name="codereview",
    help="Production-Grade AI-Powered Code Review CLI Agent",
    add_completion=False,
)
console = Console()


def version_callback(value: bool):
    if value:
        console.print(f"[bold cyan]CodeReview Agent[/bold cyan] version [green]{__version__}[/green]")
        raise typer.Exit()


def _run_review_with_progress(engine: ReviewerEngine, target_path: Path, diff: bool, category_filter: Optional[str]) -> ProjectReviewResult:
    """Run code review with interactive Rich progress bar."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}[/bold cyan]"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
        transient=True,
    ) as progress:
        task_id = progress.add_task("Scanning project...", total=100)

        def progress_cb(current: int, total: int, current_file: str):
            pct = int((current / max(1, total)) * 100)
            progress.update(
                task_id,
                completed=pct,
                description=f"Reviewing [{current}/{total}]: {current_file}",
            )

        return engine.run_review(
            target_path=target_path,
            diff_only=diff,
            category_filter=category_filter,
            progress_callback=progress_cb,
        )


@app.command("review")
def review(
    path: str = typer.Argument(
        ".",
        help="Target folder or file to review (e.g. '.', 'src/', 'app.py')",
    ),
    summary: bool = typer.Option(
        False,
        "--summary",
        "-s",
        help="Show only summary overview",
    ),
    json_out: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output raw JSON report to terminal and file",
    ),
    markdown: bool = typer.Option(
        False,
        "--markdown",
        "-m",
        help="Generate Markdown report (reports/codereview_report.md)",
    ),
    html: bool = typer.Option(
        False,
        "--html",
        "-H",
        help="Generate HTML report (reports/codereview_report.html)",
    ),
    score: bool = typer.Option(
        False,
        "--score",
        help="Show only project health score",
    ),
    security: bool = typer.Option(
        False,
        "--security",
        help="Filter review for Security vulnerabilities only",
    ),
    performance: bool = typer.Option(
        False,
        "--performance",
        help="Filter review for Performance bottlenecks only",
    ),
    architecture: bool = typer.Option(
        False,
        "--architecture",
        help="Filter review for Architecture and SOLID design rules",
    ),
    language: Optional[str] = typer.Option(
        None,
        "--language",
        "-l",
        help="Filter files by language (e.g. python, javascript, java, go)",
    ),
    fix: bool = typer.Option(
        False,
        "--fix",
        help="Display AI suggested automatic code fixes",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable detailed debug logs and output",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Run in quiet mode suppressing banners and spinners",
    ),
    diff: bool = typer.Option(
        False,
        "--diff",
        "-d",
        help="Review only git modified or staged files",
    ),
    rag: bool = typer.Option(
        False,
        "--rag",
        "-r",
        help="Enable RAG retrieval over project documentation/styleguides",
    ),
    docs_dir: Optional[str] = typer.Option(
        None,
        "--docs-dir",
        help="Custom path to documentation folder for RAG indexing",
    ),
    github_annotations: bool = typer.Option(
        False,
        "--github-annotations",
        help="Print GitHub Actions workflow annotation syntax (::warning file=...)",
    ),
    provider: Optional[str] = typer.Option(
        None,
        "--provider",
        "-p",
        help="AI provider override: openai, gemini, claude, mock",
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        help="AI model name override (e.g. gpt-4o, gemini-1.5-flash, claude-3-5-sonnet)",
    ),
    config_file: Optional[str] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to custom .codereview.toml config file",
    ),
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-V",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
):
    """
    Run an AI-powered code review on a file or project directory.
    """
    if not score and not json_out and not quiet:
        print_banner(quiet=quiet)

    # Load configuration
    cfg = load_config(config_file)
    if provider:
        cfg.provider = provider
    if model:
        cfg.model = model
    if language:
        cfg.language = language
    if rag:
        cfg.use_rag = True
    if docs_dir:
        cfg.docs_dir = docs_dir
    cfg.verbose = verbose

    # Determine category filter
    category_filter = None
    if security:
        category_filter = "security"
    elif performance:
        category_filter = "performance"
    elif architecture:
        category_filter = "architecture"

    target_path = Path(path).resolve()
    if not target_path.exists():
        Console(stderr=True).print(f"[bold red]Error:[/bold red] Target path '{path}' does not exist.")
        raise typer.Exit(code=1)

    try:
        engine = ReviewerEngine(cfg)

        if quiet:
            result: ProjectReviewResult = engine.run_review(
                target_path=target_path,
                diff_only=diff,
                category_filter=category_filter,
            )
        else:
            result = _run_review_with_progress(engine, target_path, diff, category_filter)

        # Handle GitHub Actions Annotations output
        if github_annotations:
            for issue in result.issues:
                print(format_github_actions_annotation(issue))

        # Handle --score only flag
        if score:
            console.print(f"[bold cyan]Project Health Score:[/bold cyan] [bold green]{result.scores.overall_score} / 10.0[/bold green]")
            raise typer.Exit()

        # Handle --json output
        if json_out:
            json_str = generate_json_report(result)
            console.print(json_str)
            export_reports(result, formats=["json"])
            raise typer.Exit()

        # Terminal standard output rendering
        print_scan_summary(result.scan_result, quiet=quiet)

        if not summary:
            print_issues(result.issues, quiet=quiet, verbose=verbose)

        print_scores(result.scores, quiet=quiet)
        print_review_complete_summary(result, quiet=quiet)

        # Handle report generation options (--markdown, --html)
        report_formats = []
        if markdown:
            report_formats.append("markdown")
        if html:
            report_formats.append("html")

        if report_formats and not quiet:
            saved = export_reports(result, formats=report_formats)
            console.print("\n[bold green]Reports generated successfully:[/bold green]")
            for fmt, fpath in saved.items():
                console.print(f" - [cyan]{fmt.upper()}:[/cyan] [dim]{fpath}[/dim]")

        # Check target score threshold
        if result.scores.overall_score < cfg.target_score and cfg.fail_on_high_severity and result.high_severity_count > 0:
            err_console = Console(stderr=True)
            err_console.print(
                f"\n[bold red]Review failed:[/bold red] Overall score ({result.scores.overall_score}) is below target threshold ({cfg.target_score})."
            )
            raise typer.Exit(code=2)

    except (typer.Exit, SystemExit):
        raise
    except Exception as e:
        err_console = Console(stderr=True)
        if verbose:
            err_console.print_exception()
        else:
            err_console.print(f"[bold red]Error during code review:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def history(
    limit: int = typer.Option(10, "--limit", "-n", help="Number of historical review runs to display."),
):
    """View historical project health scores and technical debt trend."""
    from app.history import HistoryManager
    manager = HistoryManager()
    manager.render_history_table(limit=limit)


def main_entrypoint():
    """CLI entrypoint wrapper ensuring backward compatibility for positional path arguments."""
    known_subcommands = {"history", "review", "help", "--help", "-h", "version", "--version", "-V"}
    if len(sys.argv) == 1:
        sys.argv.insert(1, "review")
    elif len(sys.argv) > 1 and not sys.argv[1].startswith("-") and sys.argv[1] not in known_subcommands:
        sys.argv.insert(1, "review")
    app()


if __name__ == "__main__":
    main_entrypoint()
