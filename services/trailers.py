"""Parser de trailers Git (Co-authored-by) — sem I/O."""

from __future__ import annotations

import re

from models.commit import CoAuthor, Commit

_COAUTHOR_RE = re.compile(
    r"(?im)^co-authored-by:\s*(?P<name>[^<]+?)\s*<(?P<email>[^>]+)>\s*$"
)


def parse_coauthors(message: str) -> list[CoAuthor]:
    """Lê trailers `Co-authored-by: Nome <email>` do corpo da mensagem."""
    vistos: set[str] = set()
    resultado: list[CoAuthor] = []
    for match in _COAUTHOR_RE.finditer(message):
        email = match.group("email").strip().lower()
        if not email or email in vistos:
            continue
        vistos.add(email)
        resultado.append(CoAuthor(name=match.group("name").strip(), email=email))
    return resultado


def enrich_coauthors(commit: Commit) -> Commit:
    commit.co_authors = parse_coauthors(commit.message)
    return commit
