from datetime import datetime, timedelta, timezone

from models.commit import Commit, FileChange
from services.analyzer import TIPO_NAO_PADRONIZADO, build_report
from services.conventional_commits import enrich_commit
from services.trailers import enrich_coauthors


def _dt(dia: int, hora: int = 10) -> datetime:
    return datetime(2024, 3, dia, hora, 0, tzinfo=timezone(timedelta(hours=-3)))


def _ha_dias(dias: float) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=dias)


def _commit(
    summary: str,
    email: str = "ana@example.com",
    nome: str = "Ana",
    dia: int = 15,
    hora: int = 10,
    arquivos: list[FileChange] | None = None,
    is_merge: bool = False,
    mensagem_completa: str | None = None,
    quando: datetime | None = None,
) -> Commit:
    mensagem = mensagem_completa if mensagem_completa is not None else summary
    commit = Commit(
        sha="a" * 40,
        sha_short="aaaaaaa",
        author_name=nome,
        author_email=email,
        committed_at=quando if quando is not None else _dt(dia, hora),
        message=mensagem,
        message_summary=summary,
        is_merge=is_merge,
        files_changed=arquivos or [FileChange("app.py", 10, 2)],
    )
    enrich_commit(commit)
    enrich_coauthors(commit)
    return commit


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

    def test_coautoria_aparece_no_resumo_e_no_autor(self) -> None:
        commits = [
            _commit(
                "feat: dupla",
                email="ana@example.com",
                nome="Ana",
                dia=15,
                mensagem_completa=(
                    "feat: dupla\n\nCo-authored-by: Bruno Souza <bruno@example.com>"
                ),
            ),
            _commit("fix: solo", email="bruno@example.com", nome="Bruno Souza", dia=16),
        ]
        relatorio = build_report(commits, "https://github.com/o/r")
        assert relatorio.summary.commits_with_coauthors == 1
        bruno = next(a for a in relatorio.authors if a.email == "bruno@example.com")
        assert bruno.coauthored_commit_count == 1
        ana = next(a for a in relatorio.authors if a.email == "ana@example.com")
        assert ana.coauthored_commit_count == 0

    def test_arquivo_com_dono_unico(self) -> None:
        commits = [
            _commit(
                "feat: a",
                email="ana@example.com",
                dia=15,
                arquivos=[FileChange("solo.py", 5, 0)],
            ),
            _commit(
                "feat: b",
                email="ana@example.com",
                dia=16,
                arquivos=[FileChange("solo.py", 3, 0), FileChange("compartilhado.py", 2, 0)],
            ),
            _commit(
                "feat: c",
                email="bruno@example.com",
                nome="Bruno",
                dia=17,
                arquivos=[FileChange("compartilhado.py", 1, 0)],
            ),
        ]
        relatorio = build_report(commits, "https://github.com/o/r")
        caminhos_dono_unico = {a.path for a in relatorio.file_hotspots.single_owner_files}
        assert "solo.py" in caminhos_dono_unico
        assert "compartilhado.py" not in caminhos_dono_unico
        assert relatorio.file_hotspots.single_owner_count == 1

    def test_distribuicao_de_tamanho_de_commit(self) -> None:
        commits = [
            _commit("feat: pequeno", arquivos=[FileChange("a.py", 2, 0)]),
            _commit("feat: grande", dia=16, arquivos=[FileChange("b.py", 300, 0)]),
        ]
        relatorio = build_report(commits, "https://github.com/o/r")
        contagem = {b.label: b.count for b in relatorio.commit_size_buckets}
        assert contagem["≤10"] == 1
        assert contagem["201–500"] == 1

    def test_corrida_de_ultima_hora_gera_alerta(self) -> None:
        commits = [_commit("feat: antigo", dia=1, hora=8)]
        for i in range(9):
            commits.append(_commit(f"feat: rush {i}", dia=10, hora=23))
        relatorio = build_report(commits, "https://github.com/o/r")
        kinds = {flag.kind for flag in relatorio.attention_flags}
        assert "corrida_final" in kinds

    def test_contribuicao_acumulada_cresce_por_dia(self) -> None:
        commits = [
            _commit("feat: a", email="ana@example.com", dia=15),
            _commit("feat: b", email="ana@example.com", dia=16),
            _commit("feat: c", email="ana@example.com", dia=17),
        ]
        relatorio = build_report(commits, "https://github.com/o/r")
        serie = next(
            s for s in relatorio.cumulative_contribution if s.author_email == "ana@example.com"
        )
        acumulados = [p.cumulative_commits for p in serie.points]
        assert acumulados == sorted(acumulados)
        assert acumulados[-1] == 3

    def test_fuso_horario_sao_paulo(self) -> None:
        commits = [_commit("feat: a", dia=15)]
        relatorio = build_report(commits, "https://github.com/o/r")
        assert relatorio.generated_at_sp.tzinfo is not None
        assert relatorio.generated_at_sp.utcoffset() == timedelta(hours=-3)

    def test_atividade_recente_separa_janelas(self) -> None:
        commits = [
            _commit("feat: hoje", email="ana@example.com", quando=_ha_dias(1)),
            _commit("feat: semana passada", email="ana@example.com", quando=_ha_dias(10)),
            _commit("feat: mes passado", email="ana@example.com", quando=_ha_dias(25)),
            _commit("feat: antigo", email="ana@example.com", quando=_ha_dias(60)),
        ]
        relatorio = build_report(commits, "https://github.com/o/r")
        ana = next(
            a for a in relatorio.recent_activity.authors if a.author_email == "ana@example.com"
        )
        assert ana.commits_short_window == 1
        assert ana.commits_long_window == 3
        assert ana.active_days_long_window == 3
        assert ana.days_since_last_commit == 1

    def test_atividade_recente_inclui_autor_sem_atividade(self) -> None:
        commits = [
            _commit("feat: ativo", email="ana@example.com", quando=_ha_dias(1)),
            _commit("feat: sumiu", email="bruno@example.com", nome="Bruno", quando=_ha_dias(90)),
        ]
        relatorio = build_report(commits, "https://github.com/o/r")
        bruno = next(
            a for a in relatorio.recent_activity.authors if a.author_email == "bruno@example.com"
        )
        assert bruno.commits_short_window == 0
        assert bruno.commits_long_window == 0

    def test_atividade_recente_traz_mensagens_mais_novas_primeiro(self) -> None:
        commits = [
            _commit("feat: primeiro", email="ana@example.com", quando=_ha_dias(5)),
            _commit("feat: segundo", email="ana@example.com", quando=_ha_dias(2)),
        ]
        relatorio = build_report(commits, "https://github.com/o/r")
        ana = next(
            a for a in relatorio.recent_activity.authors if a.author_email == "ana@example.com"
        )
        assert [m.summary for m in ana.recent_messages] == ["feat: segundo", "feat: primeiro"]

