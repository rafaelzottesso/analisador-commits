"""Extração de commits via uma única chamada de `git log`.

GitPython chama um subprocesso `git` por commit para calcular
`commit.stats` (insertions/deletions por arquivo). Para repositórios com
milhares de commits isso vira milhares de `fork/exec` sequenciais — o
maior gargalo medido no pipeline. Aqui o histórico inteiro é lido em um
único processo `git log --numstat` e parseado em Python.
"""

from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path

import config
from models.commit import Commit, FileChange
from services.conventional_commits import enrich_commit
from services.errors import CloneTimeoutError, EmptyRepositoryError

_MSG_VAZIO = "Este repositório não possui histórico de commits para analisar."
_MSG_TIMEOUT = (
    "A extração do histórico demorou muito. Tente novamente ou use um repositório menor."
)

# Delimitadores de controle (improváveis em mensagens de commit reais) usados
# para separar registros e campos sem ambiguidade com o corpo da mensagem,
# que pode conter qualquer texto, inclusive quebras de linha.
_RECORD_SEP = "\x1e"
_FIELD_SEP = "\x1f"
_HEADER_END = "\x02"
_PRETTY_FORMAT = (
    f"{_RECORD_SEP}%H{_FIELD_SEP}%P{_FIELD_SEP}%an{_FIELD_SEP}%ae{_FIELD_SEP}%cI{_FIELD_SEP}%B{_HEADER_END}"
)


def extract_commits(
    tmp_dir: str | Path,
    max_commits: int = config.MAX_COMMITS,
) -> tuple[list[Commit], bool]:
    saida = _git_log(tmp_dir, max_commits)
    registros = saida.split(_RECORD_SEP)[1:]  # o primeiro item antes do 1º separador é sempre vazio

    limitado = len(registros) > max_commits
    if limitado:
        registros = registros[:max_commits]

    commits = [_parse_registro(registro) for registro in registros]
    if not commits:
        raise EmptyRepositoryError(_MSG_VAZIO)
    return commits, limitado


def _git_log(tmp_dir: str | Path, max_commits: int) -> str:
    comando = [
        "git",
        "-C",
        str(tmp_dir),
        "log",
        f"-n{max_commits + 1}",
        # Diffa merges só contra o primeiro pai (equivalente ao que
        # commit.stats do GitPython fazia), em vez de --numstat padrão,
        # que não emite diff nenhum para commits de merge.
        "--diff-merges=first-parent",
        # Sem detecção de rename: cada caminho histórico soma suas próprias
        # linhas, o que é o comportamento certo para hotspots de arquivo.
        "--no-renames",
        "--numstat",
        f"--pretty=format:{_PRETTY_FORMAT}",
    ]
    try:
        resultado = subprocess.run(
            comando,
            timeout=config.PIPELINE_TIMEOUT_SECONDS,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except subprocess.TimeoutExpired as exc:
        raise CloneTimeoutError(_MSG_TIMEOUT) from exc
    if resultado.returncode != 0:
        # HEAD sem commits (repositório recém-criado) cai aqui; qualquer
        # outra falha de leitura local também é tratada como "sem histórico"
        # para manter uma mensagem única e amigável na interface.
        raise EmptyRepositoryError(_MSG_VAZIO)
    return resultado.stdout


def _parse_registro(registro: str) -> Commit:
    cabecalho, _, resto = registro.partition(_HEADER_END)
    sha, pais, author_name, author_email, committed_iso, mensagem = cabecalho.split(
        _FIELD_SEP, 5
    )
    linhas = mensagem.splitlines()
    resumo = linhas[0] if linhas else ""

    commit = Commit(
        sha=sha,
        sha_short=sha[:7],
        author_name=author_name,
        author_email=author_email,
        committed_at=datetime.fromisoformat(committed_iso),
        message=mensagem,
        message_summary=resumo,
        is_merge=len(pais.split()) > 1,
        files_changed=_file_changes(resto),
    )
    enrich_commit(commit)
    return commit


def _file_changes(bloco_numstat: str) -> list[FileChange]:
    arquivos: list[FileChange] = []
    for linha in bloco_numstat.splitlines():
        if not linha:
            continue
        partes = linha.split("\t", 2)
        if len(partes) != 3:
            continue
        ins_txt, del_txt, caminho = partes
        arquivos.append(
            FileChange(
                path=caminho,
                insertions=int(ins_txt) if ins_txt.isdigit() else 0,
                deletions=int(del_txt) if del_txt.isdigit() else 0,
            )
        )
    return arquivos
