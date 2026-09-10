"""Cria repositórios Git sintéticos para testes de cloner/extractor."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


def init_repo(caminho: Path) -> None:
    caminho.mkdir(parents=True, exist_ok=True)
    _git(caminho, "init", "-b", "main")
    _git(caminho, "config", "user.name", "Tester")
    _git(caminho, "config", "user.email", "tester@example.com")
    _git(caminho, "config", "commit.gpgsign", "false")


def add_commit(
    caminho: Path,
    message: str,
    filename: str,
    content: str,
    author_name: str = "Ana",
    author_email: str = "ana@example.com",
    date: str = "2024-03-15T10:00:00-03:00",
) -> None:
    (caminho / filename).parent.mkdir(parents=True, exist_ok=True)
    arquivo = caminho / filename
    if arquivo.exists():
        texto = arquivo.read_text(encoding="utf-8")
        arquivo.write_text(texto + content, encoding="utf-8")
    else:
        arquivo.write_text(content, encoding="utf-8")
    _git(caminho, "add", filename)
    env = os.environ.copy()
    env.update(
        {
            "GIT_AUTHOR_NAME": author_name,
            "GIT_AUTHOR_EMAIL": author_email,
            "GIT_COMMITTER_NAME": author_name,
            "GIT_COMMITTER_EMAIL": author_email,
            "GIT_AUTHOR_DATE": date,
            "GIT_COMMITTER_DATE": date,
        }
    )
    subprocess.run(
        ["git", "commit", "-m", message],
        cwd=caminho,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )


def criar_repositorio_exemplo(caminho: Path) -> None:
    init_repo(caminho)
    add_commit(
        caminho,
        "feat(auth): adiciona login",
        "app.py",
        "print('ola')\n",
        author_name="Ana",
        author_email="ana@example.com",
        date="2024-03-15T10:00:00-03:00",
    )
    add_commit(
        caminho,
        "fix(ui): corrige botao",
        "index.html",
        "<p>ok</p>\n",
        author_name="Bruno",
        author_email="bruno@example.com",
        date="2024-03-16T22:00:00-03:00",
    )
    add_commit(
        caminho,
        "ajustes diversos",
        "app.py",
        "print('mundo')\n",
        author_name="Ana Silva",
        author_email="ana@example.com",
        date="2024-03-17T09:00:00-03:00",
    )


def _git(caminho: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=caminho,
        check=True,
        capture_output=True,
        text=True,
    )
