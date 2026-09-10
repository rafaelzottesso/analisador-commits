from datetime import datetime, timedelta, timezone

from models.commit import Commit, FileChange
from services.analyzer import TIPO_NAO_PADRONIZADO, build_report
from services.conventional_commits import enrich_commit


def _dt(dia: int, hora: int = 10) -> datetime:
    return datetime(2024, 3, dia, hora, 0, tzinfo=timezone(timedelta(hours=-3)))


def _commit(
    summary: str,
    email: str = "ana@example.com",
    nome: str = "Ana",
    dia: int = 15,
    hora: int = 10,
    arquivos: list[FileChange] | None = None,
    is_merge: bool = False,
) -> Commit:
    commit = Commit(
        sha="a" * 40,
        sha_short="aaaaaaa",
        author_name=nome,
        author_email=email,
        committed_at=_dt(dia, hora),
        message=summary,
        message_summary=summary,
        is_merge=is_merge,
        files_changed=arquivos or [FileChange("app.py", 10, 2)],
    )
    return enrich_commit(commit)


class TestBuildReport:
    def test_resumo_executivo(self) -> None:
        commits = [
            _commit("feat: um", email="ana@example.com", dia=15),
            _commit("fix: dois", email="bruno@example.com", dia=16),
            _commit("sem padrao", email="ana@example.com", dia=17),
        ]
        commits[2].files_changed = [FileChange("app.py", 5, 1)]
        relatorio = build_report(commits, "https://github.com/o/r")
        assert relatorio.summary.total_commits == 3
        assert relatorio.summary.total_authors == 2
        assert relatorio.summary.conventional_adherence_pct == 66.7
        assert relatorio.summary.merge_commits == 0
        assert relatorio.summary.total_insertions == 25
        assert relatorio.summary.total_deletions == 5
        assert relatorio.summary.analysis_limited is False

    def test_autores_agrupam_por_email(self) -> None:
        commits = [
            _commit("feat: a", nome="Ana", email="ana@example.com", dia=15),
            _commit("feat: b", nome="Ana Silva", email="ana@example.com", dia=16),
            _commit("feat: c", nome="Ana Silva", email="ana@example.com", dia=17),
            _commit("feat: d", nome="Bruno", email="bruno@example.com", dia=17),
        ]
        relatorio = build_report(commits, "https://github.com/o/r")
        ana = next(a for a in relatorio.authors if a.email == "ana@example.com")
        assert ana.name == "Ana Silva"
        assert ana.commit_count == 3
        assert ana.commit_pct == 75.0

    def test_tipo_nao_padronizado(self) -> None:
        commits = [
            _commit("feat: um"),
            _commit("wip"),
        ]
        relatorio = build_report(commits, "https://github.com/o/r")
        tipos = {item.commit_type: item.count for item in relatorio.commit_types.types}
        assert tipos["feat"] == 1
        assert tipos[TIPO_NAO_PADRONIZADO] == 1

    def test_heatmap_usa_hora_local_do_commit(self) -> None:
        commits = [_commit("feat: noite", hora=22, dia=16)]
        # 16/03/2024 foi sábado (weekday=5), hora 22
        relatorio = build_report(commits, "https://github.com/o/r")
        assert relatorio.time_heatmap.matrix[5][22] == 1
        assert relatorio.time_heatmap.weekday_labels[5] == "Sábado"

    def test_hotspots_por_extensao(self) -> None:
        commits = [
            _commit(
                "feat: arquivos",
                arquivos=[
                    FileChange("app.py", 10, 0),
                    FileChange("index.html", 4, 1),
                ],
            )
        ]
        relatorio = build_report(commits, "https://github.com/o/r")
        extensoes = {e.extension: e for e in relatorio.file_hotspots.by_extension}
        assert ".py" in extensoes
        assert ".html" in extensoes
        assert extensoes[".py"].total_changed == 10

    def test_mensagem_curta_e_repetida(self) -> None:
        commits = [
            _commit("fix"),
            _commit("ajustes"),
            _commit("Ajustes!"),
            _commit("AJUSTES"),
        ]
        relatorio = build_report(commits, "https://github.com/o/r")
        kinds = {flag.kind for flag in relatorio.attention_flags}
        assert "mensagem_curta" in kinds
        assert "mensagem_repetida" in kinds

    def test_commit_enorme(self) -> None:
        commits = [
            _commit(
                "feat: lote",
                arquivos=[FileChange("big.py", 400, 150)],
            )
        ]
        relatorio = build_report(commits, "https://github.com/o/r")
        assert any(flag.kind == "commit_enorme" for flag in relatorio.attention_flags)

    def test_revert_e_concentracao(self) -> None:
        commits = [
            _commit("revert: desfaz login", email="ana@example.com", dia=15),
            _commit("feat: outro", email="ana@example.com", dia=15, hora=11),
        ]
        relatorio = build_report(commits, "https://github.com/o/r")
        kinds = {flag.kind for flag in relatorio.attention_flags}
        assert "revert" in kinds
        assert "concentracao_temporal" in kinds

    def test_outlier_na_timeline(self) -> None:
        commits = [_commit("feat: calmo", dia=10)]
        for _ in range(10):
            commits.append(_commit("feat: pico", dia=20))
        relatorio = build_report(commits, "https://github.com/o/r")
        pico = next(p for p in relatorio.timeline.points if p.date == "2024-03-20")
        calmo = next(p for p in relatorio.timeline.points if p.date == "2024-03-10")
        assert pico.is_outlier is True
        assert calmo.is_outlier is False
        assert pico.count == 10
