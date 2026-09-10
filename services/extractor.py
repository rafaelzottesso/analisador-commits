"""Extração de commits de um clone bare via GitPython."""

from __future__ import annotations

from pathlib import Path

from git import Repo

import config
from models.commit import Commit, FileChange
from services.conventional_commits import enrich_commit
from services.errors import EmptyRepositoryError


def extract_commits(
    tmp_dir: str | Path,
    max_commits: int = config.MAX_COMMITS,
) -> tuple[list[Commit], bool]:
    repositorio = Repo(str(tmp_dir))
    try:
        head_valido = repositorio.head.is_valid()
    except ValueError:
        head_valido = False
    if not head_valido:
        raise EmptyRepositoryError(
            "Este repositório não possui histórico de commits para analisar."
        )

    commits: list[Commit] = []
    limitado = False

    for indice, git_commit in enumerate(repositorio.iter_commits()):
        if indice >= max_commits:
            limitado = True
            break

        arquivos = _file_changes(git_commit)
        mensagem = _mensagem(git_commit.message)
        linhas = mensagem.splitlines()
        resumo = linhas[0] if linhas else ""

        commit = Commit(
            sha=git_commit.hexsha,
            sha_short=git_commit.hexsha[:7],
            author_name=git_commit.author.name or "",
            author_email=git_commit.author.email or "",
            committed_at=git_commit.committed_datetime,
            message=mensagem,
            message_summary=resumo,
            is_merge=len(git_commit.parents) > 1,
            files_changed=arquivos,
        )
        enrich_commit(commit)
        commits.append(commit)

    if not commits:
        raise EmptyRepositoryError(
            "Este repositório não possui histórico de commits para analisar."
        )
    return commits, limitado


def _mensagem(bruta: str | bytes | None) -> str:
    if bruta is None:
        return ""
    if isinstance(bruta, bytes):
        return bruta.decode("utf-8", errors="replace")
    return bruta


def _file_changes(git_commit: object) -> list[FileChange]:
    try:
        stats = git_commit.stats.files  # type: ignore[attr-defined]
    except (ValueError, KeyError, AttributeError):
        return []

    arquivos: list[FileChange] = []
    for caminho, dados in stats.items():
        arquivos.append(
            FileChange(
                path=str(caminho),
                insertions=int(dados.get("insertions", 0) or 0),
                deletions=int(dados.get("deletions", 0) or 0),
            )
        )
    return arquivos
