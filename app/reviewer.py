from pathlib import Path
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

from app.config import ReviewConfig, load_config
from app.scanner import Scanner, ProjectScanResult, ScannedFile
from app.utils import analyze_file_structure, FileStructureMetrics, get_git_info, GitInfo
from app.ai.base import ReviewIssue, AIResponse, BaseAIProvider
from app.ai.factory import get_ai_provider
from app.static_analysis import StaticAnalyzer
from app.cache import FileCacheManager
from app.rag import RAGEngine
from app.history import HistoryManager


class HealthScores(BaseModel):
    """Calculated sub-scores and metrics for project health assessment."""
    overall_score: float = Field(description="Weighted Overall Project Score (0.0 to 10.0)")
    security_score: float = Field(description="Security Score (40% weight)")
    maintainability_score: float = Field(description="Maintainability Score (25% weight)")
    performance_score: float = Field(description="Performance Score (15% weight)")
    code_quality_score: float = Field(description="Code Quality Score (10% weight)")
    documentation_score: float = Field(description="Documentation Score (5% weight)")
    testing_score: float = Field(description="Testing Score (5% weight)")
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
        self.static_analyzer = StaticAnalyzer(custom_rules=self.config.custom_rules)
        self.cache_manager = FileCacheManager()
        self.rag_engine = RAGEngine()

    def run_review(
        self,
        target_path: str | Path = ".",
        diff_only: bool = False,
        category_filter: Optional[str] = None,
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
                files_to_review = scan_result.files

        file_metrics_list: List[FileStructureMetrics] = []
        all_issues: List[ReviewIssue] = []
        summaries: List[str] = []

        total_files = len(files_to_review)

        for idx, scanned_file in enumerate(files_to_review, start=1):
            if progress_callback:
                progress_callback(idx, total_files, scanned_file.relative_path)

            metrics = analyze_file_structure(
                scanned_file.path, scanned_file.relative_path, scanned_file.language
            )
            file_metrics_list.append(metrics)

            file_issues: List[ReviewIssue] = []

            if self.cache_manager.is_file_unchanged(scanned_file.path, scanned_file.relative_path):
                cached_data = self.cache_manager.get_cached_issues(scanned_file.relative_path)
                file_issues = [ReviewIssue(**item) for item in cached_data]
            else:
                static_issues = self.static_analyzer.analyze_file(
                    scanned_file.path, scanned_file.relative_path, metrics.code_content, scanned_file.language
                )
                file_issues.extend(static_issues)

                rag_context = ""
                if self.rag_engine.is_indexed:
                    rag_context = self.rag_engine.retrieve_context(metrics.code_content)

                prompt_type = "rag" if rag_context else ("security" if category_filter == "security" else "general")

                ai_response: AIResponse = self.ai_provider.review_code(
                    file_path=scanned_file.relative_path,
                    code=metrics.code_content,
                    language=scanned_file.language,
                    prompt_type=prompt_type,
                    functions=metrics.functions,
                    classes=metrics.classes,
                )

                file_issues.extend(ai_response.issues)
                summaries.append(ai_response.summary)

                self.cache_manager.update_cache(scanned_file.path, scanned_file.relative_path, file_issues)

            all_issues.extend(file_issues)

        if category_filter:
            cat_low = category_filter.lower()
            all_issues = [i for i in all_issues if i.category.lower() == cat_low or cat_low in i.category.lower()]

        unique_issues: List[ReviewIssue] = []
        seen_keys = set()
        for issue in all_issues:
            key = (issue.file_path, issue.line_number, issue.title)
            if key not in seen_keys:
                seen_keys.add(key)
                unique_issues.append(issue)

        all_issues = unique_issues

        self.cache_manager.save_cache()

        high_cnt = sum(1 for i in all_issues if i.severity == "HIGH")
        med_cnt = sum(1 for i in all_issues if i.severity == "MEDIUM")
        low_cnt = sum(1 for i in all_issues if i.severity == "LOW")
        info_cnt = sum(1 for i in all_issues if i.severity == "INFO")

        scores = self._calculate_health_scores(
            file_metrics=file_metrics_list,
            issues=all_issues,
            total_lines=scan_result.total_lines,
            scan_result=scan_result,
        )

        # Auto-record review run into local SQLite history database
        try:
            history_mgr = HistoryManager()
            history_mgr.record_review(
                target_path=str(target),
                overall_score=scores.overall_score,
                security_score=scores.security_score,
                maintainability_score=scores.maintainability_score,
                quality_score=scores.code_quality_score,
                performance_score=scores.performance_score,
                doc_score=scores.documentation_score,
                test_score=scores.testing_score,
                total_files=scan_result.total_files,
                total_issues=len(all_issues),
                high_issues=high_cnt,
                technical_debt_hours=scores.estimated_technical_debt_hours,
                branch=git_info.current_branch,
            )
        except Exception:
            pass

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
        issues: List[ReviewIssue],
        total_lines: int,
        scan_result: Optional[ProjectScanResult] = None,
    ) -> HealthScores:
        """Derive weighted project health, maintainability, security, tech debt, and dynamic testing scores."""
        if file_metrics:
            avg_complexity = sum(m.complexity for m in file_metrics) / len(file_metrics)
            doc_ratio = sum(1 for m in file_metrics if m.has_docstring) / len(file_metrics)
        else:
            avg_complexity = 1.0
            doc_ratio = 1.0

        sec_issues = [i for i in issues if i.category.lower() == "security"]
        quality_issues = [i for i in issues if i.category.lower() in ("quality", "bug", "readability")]
        perf_issues = [i for i in issues if i.category.lower() == "performance"]

        # 1. Security Score (40% Weight)
        sec_penalty = sum(2.5 if i.severity == "HIGH" else (0.8 if i.severity == "MEDIUM" else 0.2) for i in sec_issues)
        sec_score = max(1.0, min(10.0, 10.0 - sec_penalty))

        # 2. Code Quality Score (25% Weight)
        quality_penalty = sum(2.0 if i.severity == "HIGH" else (0.7 if i.severity == "MEDIUM" else 0.2) for i in quality_issues)
        quality_score = max(1.0, min(10.0, 10.0 - quality_penalty))

        # 3. Maintainability Score (25% Weight)
        maint_penalty = max(0.0, (avg_complexity - 2.0) * 0.5) + sum(0.3 if i.severity == "MEDIUM" else 0.1 for i in issues)
        maint_score = max(1.0, min(10.0, 10.0 - maint_penalty))

        # 4. Performance Score (15% Weight)
        perf_penalty = sum(1.5 if i.severity == "HIGH" else (0.8 if i.severity == "MEDIUM" else 0.2) for i in perf_issues)
        perf_score = max(1.0, min(10.0, 10.0 - perf_penalty))

        # 5. Documentation Score (5% Weight)
        doc_score = max(1.0, min(10.0, doc_ratio * 10.0))

        # 6. Dynamic Testing Score (5% Weight)
        if scan_result and scan_result.files:
            test_files = [f for f in scan_result.files if f.is_test_file]
            source_files = [f for f in scan_result.files if not f.is_test_file]

            if not source_files:
                test_score = 10.0 if test_files else 1.0
            elif not test_files:
                test_score = 1.0
            else:
                file_ratio = len(test_files) / len(source_files)
                test_loc = sum(f.line_count for f in test_files)
                source_loc = sum(f.line_count for f in source_files)
                loc_ratio = test_loc / max(1, source_loc)

                hybrid_ratio = (0.5 * file_ratio) + (0.5 * loc_ratio)
                test_score = max(1.0, min(10.0, 1.0 + (hybrid_ratio / 0.40) * 9.0))
        else:
            test_score = 1.0

        # Weighted Overall Score Formula
        overall = (
            (sec_score * 0.40) +
            (maint_score * 0.25) +
            (quality_score * 0.15) +
            (perf_score * 0.10) +
            (doc_score * 0.05) +
            (test_score * 0.05)
        )
        overall = round(max(1.0, min(10.0, overall)), 1)

        debt_minutes = sum(i.estimated_fix_minutes for i in issues)
        debt_hours = round(debt_minutes / 60.0, 1)

        return HealthScores(
            overall_score=overall,
            security_score=round(sec_score, 1),
            maintainability_score=round(maint_score, 1),
            performance_score=round(perf_score, 1),
            code_quality_score=round(quality_score, 1),
            documentation_score=round(doc_score, 1),
            testing_score=round(test_score, 1),
            estimated_technical_debt_hours=debt_hours,
            average_cyclomatic_complexity=round(avg_complexity, 1),
        )
