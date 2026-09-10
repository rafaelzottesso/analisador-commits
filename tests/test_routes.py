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


def test_renderiza_relatorio_com_filtro_de_uma_data(client) -> None:
    from datetime import datetime, timezone, timedelta
    commits = [_commit("feat: um")]
    relatorio = build_report(commits, "https://github.com/o/r")
    data_limite = datetime(2024, 3, 15, 23, 59, 59, tzinfo=timezone(timedelta(hours=-3)))
    with client.application.test_request_context("/"):
        html = render_template(
            "report.html",
            report=relatorio,
            report_json=to_jsonable(relatorio),
            filtered_until=data_limite,
        )
    assert "Análise congelada até 15/03/2024" in html


def test_renderiza_tela_comparativa(client) -> None:
    from datetime import datetime, timezone, timedelta
    from services.analyzer import build_comparison_report

    f1 = [_commit("feat: fase 1")]
    f2 = [_commit("feat: fase 2", nome="Bruno", email="bruno@example.com")]
    d1 = datetime(2024, 3, 15, 23, 59, 59, tzinfo=timezone(timedelta(hours=-3)))
    d2 = datetime(2024, 3, 30, 23, 59, 59, tzinfo=timezone(timedelta(hours=-3)))

    relatorio_comp = build_comparison_report(f1, f2, [], "https://github.com/o/r", d1, d2)
    with client.application.test_request_context("/"):
        html = render_template(
            "comparison_report.html",
            report=relatorio_comp,
            report_json=to_jsonable(relatorio_comp),
        )
    assert "Relatório comparativo de fases" in html
    assert "Resumo executivo" in html
    assert "Participação por autor" in html
    assert "Pontos de atenção" in html
    assert "grafico-comparativo-autores" in html


def test_post_com_datas_invalidas(client) -> None:
    # Apenas Data 2 sem Data 1
    resposta = client.post("/analisar", data={
        "url": "https://github.com/owner/repo",
        "date_1": "",
        "date_2": "2024-03-30",
    })
    assert resposta.status_code == 400
    assert "obrigatório informar a Data 1".encode("utf-8") in resposta.data

    # Data 2 anterior à Data 1
    resposta = client.post("/analisar", data={
        "url": "https://github.com/owner/repo",
        "date_1": "2024-03-30",
        "date_2": "2024-03-15",
    })
    assert resposta.status_code == 400
    assert "deve ser posterior".encode("utf-8") in resposta.data


def test_post_analisar_e2e_com_duas_datas(client, tmp_path) -> None:
    from unittest.mock import patch
    from tests.git_helpers import add_commit, init_repo

    repo_path = tmp_path / "repo_teste_duas"
    init_repo(repo_path)
    add_commit(repo_path, "feat: commit fase 1", "f1.txt", "conteudo 1", date="2024-03-10T10:00:00-03:00")
    add_commit(repo_path, "feat: commit fase 2", "f2.txt", "conteudo 2", date="2024-03-20T10:00:00-03:00")

    with (
        patch("routes.analyzer.check_repo_size"),
        patch("routes.analyzer.clone_repository", return_value=repo_path),
        patch("routes.analyzer.cleanup_repo"),
    ):
        resposta = client.post(
            "/analisar",
            data={
                "url": "https://github.com/owner/repo",
                "date_1": "2024-03-15",
                "date_2": "2024-03-25",
            },
        )

    assert resposta.status_code == 200
    assert "Relatório comparativo de fases".encode("utf-8") in resposta.data
    assert "Fase 1: até 15/03/2024".encode("utf-8") in resposta.data
    assert "Fase 2: até 25/03/2024".encode("utf-8") in resposta.data



def test_post_analisar_e2e_com_uma_data(client, tmp_path) -> None:
    from unittest.mock import patch
    from tests.git_helpers import add_commit, init_repo

    repo_path = tmp_path / "repo_teste_uma"
    init_repo(repo_path)
    add_commit(repo_path, "feat: commit fase 1", "f1.txt", "conteudo 1", date="2024-03-10T10:00:00-03:00")
    add_commit(repo_path, "feat: commit posterior", "f2.txt", "conteudo 2", date="2024-03-20T10:00:00-03:00")

    with (
        patch("routes.analyzer.check_repo_size"),
        patch("routes.analyzer.clone_repository", return_value=repo_path),
        patch("routes.analyzer.cleanup_repo"),
    ):
        resposta = client.post(
            "/analisar",
            data={
                "url": "https://github.com/owner/repo",
                "date_1": "2024-03-15",
            },
        )

    assert resposta.status_code == 200
    assert "Análise congelada até 15/03/2024".encode("utf-8") in resposta.data



