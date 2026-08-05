from pathlib import Path
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

from app.config import ReviewConfig, load_config
from app.scanner import Scanner, ProjectScanResult, ScannedFile
from app.utils import analyze_file_structure, FileStructureMetrics, get_git_info, GitInfo
from app.ai.base import ReviewIssue, AIResponse, BaseAIProvider
from app.ai.factory import get_ai_provider
from app.rag import RAGEngine


class HealthScores(BaseModel):
    """Calculated sub-scores and metrics for project health assessment."""
    overall_score: float = Field(description="Overall Project Score (0.0 to 10.0)")
    maintainability_score: float = Field(description="Maintainability Score (0.0 to 10.0)")
    security_score: float = Field(description="Security Score (0.0 to 10.0)")
    performance_score: float = Field(description="Performance Score (0.0 to 10.0)")
    code_quality_score: float = Field(description="Code Quality Score (0.0 to 10.0)")
    estimated_technical_debt_hours: float = Field(description="Estimated debt remediation time in hours")
    average_cyclomatic_complexity: float = Field(description="Average cyclomatic complexity")


class ProjectReviewResult(BaseModel):
    """Complete Code Review Result container."""
    scan_result: ProjectScanResult
    file_metrics: List[FileStructureMetrics]
    issues: List[ReviewIssue]
    high_severity_count: int
    medium_severity_count: int
    low_severity_count: int
    info_severity_count: int
    scores: HealthScores
    summaries: List[str]
    git_info: GitInfo
    provider_name: str
    model_name: str
    rag_indexed_chunks: int = 0


class ReviewerEngine:
    """Core Orchestrator for Code Review Execution."""

    def __init__(self, config: Optional[ReviewConfig] = None):
        self.config = config or load_config()
        self.scanner = Scanner(
            ignored_folders=self.config.ignored_folders,
            ignored_files=self.config.ignored_files,
            max_file_size_kb=self.config.max_file_size_kb,
            language_filter=self.config.language,
        )
        self.ai_provider: BaseAIProvider = get_ai_provider(self.config)
        self.rag_engine = RAGEngine()

    def run_review(
        self,
        target_path: str | Path = ".",
        diff_only: bool = False,
        progress_callback=None,
    ) -> ProjectReviewResult:
        """Run complete code review workflow on target path."""
        target = Path(target_path).resolve()
        scan_result = self.scanner.scan(target)
        git_info = get_git_info(target if target.is_dir() else target.parent)

        # Initialize RAG if requested
        rag_indexed_count = 0
        if self.config.use_rag or self.config.docs_dir:
            docs_folder = Path(self.config.docs_dir).resolve() if self.config.docs_dir else (target if target.is_dir() else target.parent)
            rag_indexed_count = self.rag_engine.index_directory(docs_folder)

        # Filter files if --diff flag requested
        files_to_review = scan_result.files
        if diff_only and git_info.is_git_repo:
            changed_set = set(git_info.modified_files + git_info.staged_files)
            files_to_review = [
                f for f in scan_result.files
                if any(f.relative_path.endswith(chg) or chg.endswith(f.relative_path) for chg in changed_set)
            ]
            if not files_to_review:
                # If no matches found, default back to scanned files with a warning
                files_to_review = scan_result.files

        file_metrics_list: List[FileStructureMetrics] = []
        all_issues: List[ReviewIssue] = []
        summaries: List[str] = []

        total_files = len(files_to_review)

        for idx, scanned_file in enumerate(files_to_review, start=1):
            if progress_callback:
                progress_callback(idx, total_files, scanned_file.relative_path)

            # 1. Structural static AST analysis
            metrics = analyze_file_structure(
                scanned_file.path, scanned_file.relative_path, scanned_file.language
            )
            file_metrics_list.append(metrics)

            # 2. AI Review
            rag_context = ""
            if self.rag_engine.is_indexed:
                rag_context = self.rag_engine.retrieve_context(metrics.code_content)

            prompt_type = "rag" if rag_context else "general"

            ai_response: AIResponse = self.ai_provider.review_code(
                file_path=scanned_file.relative_path,
                code=metrics.code_content,
                language=scanned_file.language,
                prompt_type=prompt_type,
                functions=metrics.functions,
                classes=metrics.classes,
            )

            all_issues.extend(ai_response.issues)
            summaries.append(ai_response.summary)

        # Count severities
        high_cnt = sum(1 for i in all_issues if i.severity == "HIGH")
        med_cnt = sum(1 for i in all_issues if i.severity == "MEDIUM")
        low_cnt = sum(1 for i in all_issues if i.severity == "LOW")
        info_cnt = sum(1 for i in all_issues if i.severity == "INFO")

        # Calculate scores & metrics
        scores = self._calculate_health_scores(
            file_metrics=file_metrics_list,
            high_count=high_cnt,
            med_count=med_cnt,
            low_count=low_cnt,
            info_count=info_cnt,
            total_lines=scan_result.total_lines,
        )

        return ProjectReviewResult(
            scan_result=scan_result,
            file_metrics=file_metrics_list,
            issues=all_issues,
            high_severity_count=high_cnt,
            medium_severity_count=med_cnt,
            low_severity_count=low_cnt,
            info_severity_count=info_cnt,
            scores=scores,
            summaries=summaries,
            git_info=git_info,
            provider_name=getattr(self.ai_provider, "provider_name", self.config.provider),
            model_name=getattr(self.ai_provider, "model", self.config.model),
            rag_indexed_chunks=rag_indexed_count,
        )

    def _calculate_health_scores(
        self,
        file_metrics: List[FileStructureMetrics],
        high_count: int,
        med_count: int,
        low_count: int,
        info_count: int,
        total_lines: int,
    ) -> HealthScores:
        """Derive project health, maintainability, security, and tech debt scores."""
        # Calculate Average Complexity
        if file_metrics:
            avg_complexity = sum(m.complexity for m in file_metrics) / len(file_metrics)
        else:
            avg_complexity = 1.0

        # Sub-score penalties based on issue severity counts
        sec_penalty = (high_count * 2.5) + (med_count * 0.8)
        perf_penalty = (high_count * 1.5) + (med_count * 1.0) + (low_count * 0.2)
        maint_penalty = (avg_complexity * 0.4) + (med_count * 0.5) + (low_count * 0.2)
        quality_penalty = (high_count * 2.0) + (med_count * 0.7) + (low_count * 0.3)

        sec_score = max(1.0, min(10.0, 10.0 - sec_penalty))
        perf_score = max(1.0, min(10.0, 10.0 - perf_penalty))
        maint_score = max(1.0, min(10.0, 10.0 - maint_penalty))
        quality_score = max(1.0, min(10.0, 10.0 - quality_penalty))

        # Overall weighted score
        overall = (sec_score * 0.35) + (quality_score * 0.25) + (maint_score * 0.25) + (perf_score * 0.15)
        overall = round(max(1.0, min(10.0, overall)), 1)

        # Technical debt estimation in hours (High=4h, Med=1.5h, Low=0.5h, Info=0.1h + complexity factor)
        debt_hours = (high_count * 4.0) + (med_count * 1.5) + (low_count * 0.5) + (info_count * 0.1)
        if avg_complexity > 10:
            debt_hours += (avg_complexity - 10) * 0.5

        return HealthScores(
            overall_score=overall,
            maintainability_score=round(maint_score, 1),
            security_score=round(sec_score, 1),
            performance_score=round(perf_score, 1),
            code_quality_score=round(quality_score, 1),
            estimated_technical_debt_hours=round(debt_hours, 1),
            average_cyclomatic_complexity=round(avg_complexity, 1),
        )
