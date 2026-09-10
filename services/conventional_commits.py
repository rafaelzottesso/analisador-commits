"""Parser puro de Conventional Commits — sem I/O."""

from __future__ import annotations

import re

from models.commit import Commit, ConventionalCommitParse

CONVENTIONAL_COMMIT_RE = re.compile(
    r"^(?P<type>feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)"
    r"(\((?P<scope>[\w\-/]+)\))?"
    r"(?P<breaking>!)?"
    r":\s(?P<description>.+)$"
)


def parse_conventional_commit(message_summary: str) -> ConventionalCommitParse:
    """Interpreta só a primeira linha; o restante da mensagem não entra no padrão."""
    match = CONVENTIONAL_COMMIT_RE.match(message_summary.strip())
    if not match:
        return ConventionalCommitParse(
            is_conventional=False,
            cc_type=None,
            cc_scope=None,
            cc_description=None,
            is_breaking=False,
        )
    return ConventionalCommitParse(
        is_conventional=True,
        cc_type=match.group("type"),
        cc_scope=match.group("scope"),
        cc_description=match.group("description"),
        is_breaking=match.group("breaking") == "!",
    )


def enrich_commit(commit: Commit) -> Commit:
    parsed = parse_conventional_commit(commit.message_summary)
    commit.is_conventional = parsed.is_conventional
    commit.cc_type = parsed.cc_type
    commit.cc_scope = parsed.cc_scope
    commit.cc_description = parsed.cc_description
    return commit
