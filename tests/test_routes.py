from flask import render_template

from services.analyzer import build_report
from services.serialize import to_jsonable
from tests.test_analyzer import _commit


def test_pagina_inicial(client) -> None:
    resposta = client.get("/")
    assert resposta.status_code == 200
    assert "Analisar".encode("utf-8") in resposta.data
    assert b"github.com" in resposta.data


def test_url_de_outro_host(client) -> None:
    resposta = client.post("/analisar", data={"url": "https://gitlab.com/owner/repo"})
    assert resposta.status_code == 400
    assert "GitHub".encode("utf-8") in resposta.data


def test_url_malformada(client) -> None:
    resposta = client.post("/analisar", data={"url": "https://github.com/so-owner"})
    assert resposta.status_code == 400
    assert "URL inválida".encode("utf-8") in resposta.data


def test_renderiza_relatorio(client) -> None:
    commits = [
        _commit("feat: um", email="ana@example.com"),
        _commit("fix: dois", email="bruno@example.com", nome="Bruno", dia=16),
    ]
    relatorio = build_report(commits, "https://github.com/o/r")
    with client.application.test_request_context("/"):
        html = render_template(
            "report.html",
            report=relatorio,
            report_json=to_jsonable(relatorio),
        )
    assert "Resumo executivo" in html
    assert "Participação por autor" in html
    assert "Pontos de atenção" in html
    assert "grafico-heatmap" in html
    assert "(UTC-3)" in html

