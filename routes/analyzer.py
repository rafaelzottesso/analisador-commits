"""Rotas do formulário e da orquestração do pipeline."""

from __future__ import annotations

import logging
import time

from flask import Blueprint, render_template, request

import config
from services.analyzer import (
    build_comparison_report,
    build_report,
    filter_commits_until,
    split_commits_by_phases,
)
from services.cleanup import cleanup_repo
from services.cloner import clone_repository
from services.errors import AnalyzerError, CloneTimeoutError
from services.extractor import extract_commits
from services.serialize import to_jsonable
from services.validators import check_repo_size, parse_date_filters, parse_github_url

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
        date_1_raw = request.form.get("date_1")
        date_2_raw = request.form.get("date_2")
        dt_1, dt_2 = parse_date_filters(date_1_raw, date_2_raw)

        check_repo_size(repo)
        _garantir_tempo(inicio)
        tmp_dir = clone_repository(repo.canonical_url)
        _garantir_tempo(inicio)
        commits, limitado = extract_commits(tmp_dir)
        _garantir_tempo(inicio)
        url_exibicao = f"https://github.com/{repo.owner}/{repo.name}"

        # Comparação entre duas fases
        if dt_1 is not None and dt_2 is not None:
            f1, f2, after = split_commits_by_phases(commits, dt_1, dt_2)
            relatorio_comp = build_comparison_report(
                f1, f2, after, url_exibicao, dt_1, dt_2
            )
            return render_template(
                "comparison_report.html",
                report=relatorio_comp,
                report_json=to_jsonable(relatorio_comp),
            )

        # Relatório padrão congelado até a Data 1
        if dt_1 is not None:
            commits_filtrados = filter_commits_until(commits, dt_1)
            if not commits_filtrados:
                raise AnalyzerError(
                    f"Nenhum commit encontrado no repositório até a data limite informada ({dt_1.strftime('%d/%m/%Y')})."
                )
            relatorio = build_report(commits_filtrados, url_exibicao, limitado)
            return render_template(
                "report.html",
                report=relatorio,
                report_json=to_jsonable(relatorio),
                filtered_until=dt_1,
            )

        # Relatório padrão com todo o histórico
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
