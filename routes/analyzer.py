"""Rotas do formulário e da orquestração do pipeline."""

from __future__ import annotations

import logging
import time

from flask import Blueprint, render_template, request

import config
from services.analyzer import build_report
from services.cleanup import cleanup_repo
from services.cloner import clone_repository
from services.errors import AnalyzerError, CloneTimeoutError
from services.extractor import extract_commits
from services.serialize import to_jsonable
from services.validators import check_repo_size, parse_github_url

bp = Blueprint("analyzer", __name__)
logger = logging.getLogger(__name__)

_MSG_INESPERADO = (
    "Ocorreu um erro inesperado ao analisar o repositório. Tente novamente."
)
_MSG_PIPELINE_TIMEOUT = (
    "O repositório demorou muito para ser clonado. "
    "Tente novamente ou use um repositório menor."
)


@bp.get("/")
def index() -> str:
    return render_template("index.html")


@bp.post("/analisar")
def analisar() -> tuple[str, int] | str:
    tmp_dir = None
    inicio = time.monotonic()
    try:
        url = request.form.get("url", "")
        repo = parse_github_url(url)
        check_repo_size(repo)
        _garantir_tempo(inicio)
        tmp_dir = clone_repository(repo.canonical_url)
        _garantir_tempo(inicio)
        commits, limitado = extract_commits(tmp_dir)
        _garantir_tempo(inicio)
        url_exibicao = f"https://github.com/{repo.owner}/{repo.name}"
        relatorio = build_report(commits, url_exibicao, limitado)
        return render_template(
            "report.html",
            report=relatorio,
            report_json=to_jsonable(relatorio),
        )
    except AnalyzerError as exc:
        return render_template(
            "partials/error.html",
            mensagem=exc.user_message,
        ), 400
    except Exception:
        logger.exception("Erro inesperado na análise")
        return render_template(
            "partials/error.html",
            mensagem=_MSG_INESPERADO,
        ), 500
    finally:
        cleanup_repo(tmp_dir)


def _garantir_tempo(inicio: float) -> None:
    if time.monotonic() - inicio > config.PIPELINE_TIMEOUT_SECONDS:
        raise CloneTimeoutError(_MSG_PIPELINE_TIMEOUT)
