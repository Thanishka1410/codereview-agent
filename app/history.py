import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from rich.table import Table
from rich.console import Console
from pydantic import BaseModel

console = Console()


class HistoryRecord(BaseModel):
    """Data model representing a historical code review run."""
    id: int
    timestamp: str
    target_path: str
    branch: Optional[str]
    commit_hash: Optional[str]
    overall_score: float
    security_score: float
    maintainability_score: float
    quality_score: float
    performance_score: float
    doc_score: float
    test_score: float
    total_files: int
    total_issues: int
    high_issues: int
    technical_debt_hours: float


class HistoryManager:
    """Manages SQLite storage for review history and trend tracking."""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path:
            self.db_path = db_path
        else:
            self.db_path = Path.cwd() / ".codereview_history.db"

        self._init_db()

    def _init_db(self):
        """Initialize SQLite database schema."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS review_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    target_path TEXT NOT NULL,
                    branch TEXT,
                    commit_hash TEXT,
                    overall_score REAL NOT NULL,
                    security_score REAL NOT NULL,
                    maintainability_score REAL NOT NULL,
                    quality_score REAL NOT NULL,
                    performance_score REAL NOT NULL,
                    doc_score REAL NOT NULL,
                    test_score REAL NOT NULL,
                    total_files INTEGER NOT NULL,
                    total_issues INTEGER NOT NULL,
                    high_issues INTEGER NOT NULL,
                    technical_debt_hours REAL NOT NULL
                )
                """
            )
            conn.commit()

    def record_review(
        self,
        target_path: str,
        overall_score: float,
        security_score: float,
        maintainability_score: float,
        quality_score: float,
        performance_score: float,
        doc_score: float,
        test_score: float,
        total_files: int,
        total_issues: int,
        high_issues: int,
        technical_debt_hours: float,
        branch: Optional[str] = None,
        commit_hash: Optional[str] = None,
    ) -> int:
        """Log a completed code review run into the local SQLite database."""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO review_history (
                    timestamp, target_path, branch, commit_hash,
                    overall_score, security_score, maintainability_score,
                    quality_score, performance_score, doc_score, test_score,
                    total_files, total_issues, high_issues, technical_debt_hours
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    now_str, target_path, branch or "main", commit_hash or "N/A",
                    overall_score, security_score, maintainability_score,
                    quality_score, performance_score, doc_score, test_score,
                    total_files, total_issues, high_issues, technical_debt_hours,
                ),
            )
            conn.commit()
            return cursor.lastrowid

    def get_history(self, limit: int = 10) -> List[HistoryRecord]:
        """Fetch past review history records ordered by recency."""
        records: List[HistoryRecord] = []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM review_history ORDER BY id DESC LIMIT ?", (limit,)
            )
            rows = cursor.fetchall()
            for row in rows:
                records.append(
                    HistoryRecord(
                        id=row["id"],
                        timestamp=row["timestamp"],
                        target_path=row["target_path"],
                        branch=row["branch"],
                        commit_hash=row["commit_hash"],
                        overall_score=row["overall_score"],
                        security_score=row["security_score"],
                        maintainability_score=row["maintainability_score"],
                        quality_score=row["quality_score"],
                        performance_score=row["performance_score"],
                        doc_score=row["doc_score"],
                        test_score=row["test_score"],
                        total_files=row["total_files"],
                        total_issues=row["total_issues"],
                        high_issues=row["high_issues"],
                        technical_debt_hours=row["technical_debt_hours"],
                    )
                )
        return records

    def render_history_table(self, limit: int = 10):
        """Render formatted Rich table of review history and trend metrics."""
        history = self.get_history(limit)
        if not history:
            console.print("[dim]No historical review records found in database.[/dim]")
            return

        table = Table(title="CodeReview Historical Health & Technical Debt Trend", header_style="bold cyan")
        table.add_column("ID", justify="right", style="dim")
        table.add_column("Timestamp", justify="center")
        table.add_column("Branch", justify="center", style="green")
        table.add_column("Commit", justify="center", style="dim")
        table.add_column("Health Score", justify="center", style="bold yellow")
        table.add_column("Security", justify="center")
        table.add_column("Files", justify="right")
        table.add_column("Issues (HIGH)", justify="center")
        table.add_column("Tech Debt", justify="right")

        for r in history:
            score_color = "green" if r.overall_score >= 8.5 else ("yellow" if r.overall_score >= 7.0 else "red")
            high_color = "red" if r.high_issues > 0 else "green"

            table.add_row(
                str(r.id),
                r.timestamp,
                r.branch or "main",
                (r.commit_hash or "N/A")[:7],
                f"[{score_color}]{r.overall_score:.1f} / 10.0[/{score_color}]",
                f"{r.security_score:.1f}",
                str(r.total_files),
                f"{r.total_issues} ([{high_color}]{r.high_issues} HIGH[/{high_color}])",
                f"{r.technical_debt_hours:.1f}h",
            )

        console.print(table)
