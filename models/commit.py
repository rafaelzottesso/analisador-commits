"""Dataclasses de domínio — só dados, sem lógica de negócio."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class FileChange:
    path: str
    insertions: int
    deletions: int


@dataclass
class CoAuthor:
    name: str
    email: str


@dataclass
class Commit:
    sha: str
    sha_short: str
    author_name: str
    author_email: str
    committed_at: datetime
    message: str
    message_summary: str
    is_merge: bool
    files_changed: list[FileChange] = field(default_factory=list)
    co_authors: list[CoAuthor] = field(default_factory=list)
    cc_type: str | None = None
    cc_scope: str | None = None
    cc_description: str | None = None
    is_conventional: bool = False


@dataclass
class ConventionalCommitParse:
    is_conventional: bool
    cc_type: str | None
    cc_scope: str | None
    cc_description: str | None
    is_breaking: bool = False


@dataclass
class GitHubRepo:
    owner: str
    name: str
    canonical_url: str


@dataclass
class SummaryStats:
    total_commits: int
    total_authors: int
    period_start: datetime
    period_end: datetime
    total_insertions: int
    total_deletions: int
    conventional_adherence_pct: float
    merge_commits: int
    direct_commits: int
    analysis_limited: bool
    max_commits_limit: int | None
    commits_with_coauthors: int
    last_window_commits: int
    last_window_pct: float
    last_window_hours: int


@dataclass
class TypeCount:
    commit_type: str
    count: int
    percentage: float = 0.0


@dataclass
class AuthorStats:
    email: str
    name: str
    commit_count: int
    commit_pct: float
    insertions: int
    deletions: int
    total_changed: int
    first_commit_at: datetime
    last_commit_at: datetime
    top_commit_types: list[TypeCount]
    low_participation: bool
    coauthored_commit_count: int


@dataclass
class AuthorTypeCount:
    author_email: str
    author_name: str
    commit_type: str
    count: int


@dataclass
class ScopeCount:
    scope: str
    count: int


@dataclass
class CommitTypeStats:
    types: list[TypeCount]
    by_author: list[AuthorTypeCount]
    with_scope_count: int
    top_scopes: list[ScopeCount]


@dataclass
class AuthorCount:
    author_email: str
    author_name: str
    count: int


@dataclass
class TimelinePoint:
    date: str
    count: int
    is_outlier: bool
    by_author: list[AuthorCount]


@dataclass
class TimelineData:
    points: list[TimelinePoint]
    note: str


@dataclass
class HeatmapData:
    matrix: list[list[int]]
    weekday_labels: list[str]
    note: str


@dataclass
class FileStats:
    path: str
    commit_count: int
    insertions: int
    deletions: int
    total_changed: int
    author_count: int


@dataclass
class ExtensionStats:
    extension: str
    commit_count: int
    total_changed: int


@dataclass
class FileAuthorCross:
    path: str
    author_email: str
    author_name: str
    commit_count: int


@dataclass
class FileHotspotStats:
    top_by_commits: list[FileStats]
    top_by_lines: list[FileStats]
    by_extension: list[ExtensionStats]
    file_author_cross: list[FileAuthorCross]
    single_owner_files: list[FileStats]
    single_owner_count: int


@dataclass
class CommitSizeBucket:
    label: str
    count: int


@dataclass
class CumulativePoint:
    date: str
    cumulative_commits: int


@dataclass
class AuthorTimelineSeries:
    author_email: str
    author_name: str
    points: list[CumulativePoint]


@dataclass
class AttentionFlag:
    kind: str
    message: str
    details: str


@dataclass
class ReportData:
    summary: SummaryStats
    authors: list[AuthorStats]
    cumulative_contribution: list[AuthorTimelineSeries]
    commit_types: CommitTypeStats
    timeline: TimelineData
    commit_size_buckets: list[CommitSizeBucket]
    time_heatmap: HeatmapData
    file_hotspots: FileHotspotStats
    attention_flags: list[AttentionFlag]
    repo_url: str
    generated_at: datetime

    @property
    def generated_at_sp(self) -> datetime:
        """Data e hora de geração no fuso horário de São Paulo (UTC-3)."""
        from datetime import timedelta, timezone
        fuso_sp = timezone(timedelta(hours=-3))
        if self.generated_at.tzinfo is None:
            return self.generated_at.replace(tzinfo=timezone.utc).astimezone(fuso_sp)
        return self.generated_at.astimezone(fuso_sp)

