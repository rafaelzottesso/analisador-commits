"""Agregações do relatório a partir da lista de Commit já enriquecida."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

import config
from models.commit import (
    AttentionFlag,
    AuthorCount,
    AuthorStats,
    AuthorTimelineSeries,
    AuthorTypeCount,
    Commit,
    CommitSizeBucket,
    CommitTypeStats,
    CumulativePoint,
    ExtensionStats,
    FileAuthorCross,
    FileHotspotStats,
    FileStats,
    HeatmapData,
    ReportData,
    ScopeCount,
    SummaryStats,
    TimelineData,
    TimelinePoint,
    TypeCount,
)

TIPO_NAO_PADRONIZADO = "não padronizado"
DIAS_SEMANA = [
    "Segunda",
    "Terça",
    "Quarta",
    "Quinta",
    "Sexta",
    "Sábado",
    "Domingo",
]
NOTA_FUSO = (
    "Os horários e as datas seguem o fuso registrado em cada commit, "
    "não um fuso fixo (por exemplo America/Sao_Paulo)."
)
_PONTUACAO_RE = re.compile(r"[^\w\s]", re.UNICODE)


def build_report(
    commits: list[Commit],
    repo_url: str,
    analysis_limited: bool = False,
) -> ReportData:
    if not commits:
        raise ValueError("build_report exige ao menos um commit")

    return ReportData(
        summary=_resumo(commits, analysis_limited),
        authors=_autores(commits),
        cumulative_contribution=_contribuicao_acumulada(commits),
        commit_types=_tipos(commits),
        timeline=_linha_do_tempo(commits),
        commit_size_buckets=_tamanho_commits(commits),
        time_heatmap=_heatmap(commits),
        file_hotspots=_hotspots(commits),
        attention_flags=_pontos_de_atencao(commits),
        repo_url=repo_url,
        generated_at=datetime.now(timezone.utc),
    )


def _tipo(commit: Commit) -> str:
    if commit.is_conventional and commit.cc_type:
        return commit.cc_type
    return TIPO_NAO_PADRONIZADO


def _linhas(commit: Commit) -> tuple[int, int]:
    insercoes = sum(arquivo.insertions for arquivo in commit.files_changed)
    remocoes = sum(arquivo.deletions for arquivo in commit.files_changed)
    return insercoes, remocoes


def _percentual(parte: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(100.0 * parte / total, 1)


def _janela_final(commits: list[Commit], horas: int) -> list[Commit]:
    """Commits dentro das últimas `horas` a partir do commit mais recente."""
    fim = max(commit.committed_at for commit in commits)
    limite = fim - timedelta(hours=horas)
    return [commit for commit in commits if commit.committed_at >= limite]


def _resumo(commits: list[Commit], limitado: bool) -> SummaryStats:
    emails = {commit.author_email for commit in commits}
    insercoes = remocoes = 0
    merges = 0
    conventional = 0
    com_coautoria = 0
    for commit in commits:
        ins, dele = _linhas(commit)
        insercoes += ins
        remocoes += dele
        if commit.is_merge:
            merges += 1
        if commit.is_conventional:
            conventional += 1
        if commit.co_authors:
            com_coautoria += 1

    datas = [commit.committed_at for commit in commits]
    janela = _janela_final(commits, config.LAST_WINDOW_HOURS)
    return SummaryStats(
        total_commits=len(commits),
        total_authors=len(emails),
        period_start=min(datas),
        period_end=max(datas),
        total_insertions=insercoes,
        total_deletions=remocoes,
        conventional_adherence_pct=_percentual(conventional, len(commits)),
        merge_commits=merges,
        direct_commits=len(commits) - merges,
        analysis_limited=limitado,
        max_commits_limit=config.MAX_COMMITS if limitado else None,
        commits_with_coauthors=com_coautoria,
        last_window_commits=len(janela),
        last_window_pct=_percentual(len(janela), len(commits)),
        last_window_hours=config.LAST_WINDOW_HOURS,
    )


def _autores(commits: list[Commit]) -> list[AuthorStats]:
    por_email: dict[str, list[Commit]] = defaultdict(list)
    for commit in commits:
        por_email[commit.author_email].append(commit)

    coautoria_count: Counter[str] = Counter()
    for commit in commits:
        for coautor in commit.co_authors:
            coautoria_count[coautor.email] += 1

    total = len(commits)
    n_autores = len(por_email)
    limiar = config.participation_threshold_pct(n_autores)
    resultado: list[AuthorStats] = []

    for email, grupo in por_email.items():
        nomes = Counter(commit.author_name for commit in grupo)
        nome = nomes.most_common(1)[0][0]
        insercoes = remocoes = 0
        tipos: Counter[str] = Counter()
        for commit in grupo:
            ins, dele = _linhas(commit)
            insercoes += ins
            remocoes += dele
            tipos[_tipo(commit)] += 1
        datas = [commit.committed_at for commit in grupo]
        pct = _percentual(len(grupo), total)
        resultado.append(
            AuthorStats(
                email=email,
                name=nome,
                commit_count=len(grupo),
                commit_pct=pct,
                insertions=insercoes,
                deletions=remocoes,
                total_changed=insercoes + remocoes,
                first_commit_at=min(datas),
                last_commit_at=max(datas),
                top_commit_types=[
                    TypeCount(commit_type=tipo, count=qtd, percentage=_percentual(qtd, len(grupo)))
                    for tipo, qtd in tipos.most_common()
                ],
                low_participation=pct < limiar,
                coauthored_commit_count=coautoria_count.get(email, 0),
            )
        )

    resultado.sort(key=lambda autor: autor.commit_count, reverse=True)
    return resultado


def _contribuicao_acumulada(commits: list[Commit]) -> list[AuthorTimelineSeries]:
    """Commits acumulados ao longo do tempo para os autores mais ativos."""
    calendario = _calendario(commits)
    por_autor: dict[str, list[Commit]] = defaultdict(list)
    nomes: dict[str, str] = {}
    for commit in commits:
        por_autor[commit.author_email].append(commit)
        nomes[commit.author_email] = commit.author_name

    top_emails = [
        email
        for email, _ in sorted(
            por_autor.items(), key=lambda item: len(item[1]), reverse=True
        )[: config.CUMULATIVE_TOP_AUTHORS]
    ]

    series: list[AuthorTimelineSeries] = []
    for email in top_emails:
        por_dia: Counter[str] = Counter(
            commit.committed_at.date().isoformat() for commit in por_autor[email]
        )
        acumulado = 0
        pontos: list[CumulativePoint] = []
        for dia in calendario:
            acumulado += por_dia.get(dia.date().isoformat(), 0)
            pontos.append(CumulativePoint(date=dia.date().isoformat(), cumulative_commits=acumulado))
        series.append(
            AuthorTimelineSeries(author_email=email, author_name=nomes[email], points=pontos)
        )
    return series


def _tipos(commits: list[Commit]) -> CommitTypeStats:
    total = len(commits)
    contagem: Counter[str] = Counter(_tipo(commit) for commit in commits)
    tipos = [
        TypeCount(
            commit_type=tipo,
            count=qtd,
            percentage=_percentual(qtd, total),
        )
        for tipo, qtd in contagem.most_common()
    ]

    cruzado: Counter[tuple[str, str, str]] = Counter()
    nomes: dict[str, str] = {}
    for commit in commits:
        nomes[commit.author_email] = commit.author_name
        cruzado[(commit.author_email, commit.author_name, _tipo(commit))] += 1

    por_autor = [
        AuthorTypeCount(
            author_email=email,
            author_name=nome,
            commit_type=tipo,
            count=qtd,
        )
        for (email, nome, tipo), qtd in cruzado.most_common()
    ]

    com_escopo = sum(1 for commit in commits if commit.cc_scope)
    escopos = Counter(
        commit.cc_scope for commit in commits if commit.cc_scope
    )
    top_escopos = [
        ScopeCount(scope=escopo, count=qtd) for escopo, qtd in escopos.most_common()
    ]
    return CommitTypeStats(
        types=tipos,
        by_author=por_autor,
        with_scope_count=com_escopo,
        top_scopes=top_escopos,
    )


def _calendario(commits: list[Commit]) -> pd.DatetimeIndex:
    inicio = min(commit.committed_at.date() for commit in commits)
    fim = max(commit.committed_at.date() for commit in commits)
    return pd.date_range(inicio, fim, freq="D")


def _linha_do_tempo(commits: list[Commit]) -> TimelineData:
    registros = []
    for commit in commits:
        data = commit.committed_at.date().isoformat()
        registros.append(
            {
                "date": data,
                "author_email": commit.author_email,
                "author_name": commit.author_name,
            }
        )
    quadro = pd.DataFrame(registros)
    por_dia = quadro.groupby("date").size()

    calendario = _calendario(commits)
    serie = pd.Series(
        [int(por_dia.get(dia.date().isoformat(), 0)) for dia in calendario]
    )
    media = float(serie.mean())
    desvio = float(serie.std(ddof=0)) if len(serie) > 1 else 0.0
    limiar = media + 2 * desvio if desvio > 0 else float("inf")

    por_autor_dia: dict[str, Counter[tuple[str, str]]] = defaultdict(Counter)
    for linha in registros:
        por_autor_dia[linha["date"]][(linha["author_email"], linha["author_name"])] += 1

    pontos: list[TimelinePoint] = []
    for dia in calendario:
        chave = dia.date().isoformat()
        qtd = int(por_dia.get(chave, 0))
        autores = [
            AuthorCount(author_email=email, author_name=nome, count=n)
            for (email, nome), n in por_autor_dia[chave].most_common()
        ]
        pontos.append(
            TimelinePoint(
                date=chave,
                count=qtd,
                is_outlier=qtd > limiar,
                by_author=autores,
            )
        )
    return TimelineData(points=pontos, note=NOTA_FUSO)


def _rotulos_buckets(limites: list[int]) -> list[str]:
    rotulos = []
    anterior = 0
    for limite in limites:
        rotulos.append(f"≤{limite}" if anterior == 0 else f"{anterior}–{limite}")
        anterior = limite + 1
    rotulos.append(f"{anterior}+")
    return rotulos


def _tamanho_commits(commits: list[Commit]) -> list[CommitSizeBucket]:
    limites = config.COMMIT_SIZE_BUCKET_EDGES
    rotulos = _rotulos_buckets(limites)
    contagem = [0] * len(rotulos)
    for commit in commits:
        ins, dele = _linhas(commit)
        total = ins + dele
        indice = next(
            (i for i, limite in enumerate(limites) if total <= limite), len(limites)
        )
        contagem[indice] += 1
    return [
        CommitSizeBucket(label=rotulo, count=qtd) for rotulo, qtd in zip(rotulos, contagem)
    ]


def _heatmap(commits: list[Commit]) -> HeatmapData:
    matriz = [[0 for _ in range(24)] for _ in range(7)]
    for commit in commits:
        instante = commit.committed_at
        matriz[instante.weekday()][instante.hour] += 1
    return HeatmapData(matrix=matriz, weekday_labels=DIAS_SEMANA, note=NOTA_FUSO)


def _hotspots(commits: list[Commit]) -> FileHotspotStats:
    por_arquivo: dict[str, dict[str, int]] = defaultdict(
        lambda: {"commits": 0, "insertions": 0, "deletions": 0}
    )
    autores_por_arquivo: dict[str, set[str]] = defaultdict(set)
    por_extensao: dict[str, dict[str, int]] = defaultdict(
        lambda: {"commits": 0, "changed": 0}
    )
    cruzamento: Counter[tuple[str, str, str]] = Counter()

    for commit in commits:
        vistos: set[str] = set()
        extensoes_vistas: set[str] = set()
        for arquivo in commit.files_changed:
            stats = por_arquivo[arquivo.path]
            stats["commits"] += 1
            stats["insertions"] += arquivo.insertions
            stats["deletions"] += arquivo.deletions
            autores_por_arquivo[arquivo.path].add(commit.author_email)
            cruzamento[(arquivo.path, commit.author_email, commit.author_name)] += 1
            vistos.add(arquivo.path)
            extensao = Path(arquivo.path).suffix.lower() or "(sem extensão)"
            if extensao not in extensoes_vistas:
                por_extensao[extensao]["commits"] += 1
                extensoes_vistas.add(extensao)
            por_extensao[extensao]["changed"] += arquivo.insertions + arquivo.deletions

    arquivos = [
        FileStats(
            path=caminho,
            commit_count=dados["commits"],
            insertions=dados["insertions"],
            deletions=dados["deletions"],
            total_changed=dados["insertions"] + dados["deletions"],
            author_count=len(autores_por_arquivo[caminho]),
        )
        for caminho, dados in por_arquivo.items()
    ]
    top_commits = sorted(arquivos, key=lambda item: item.commit_count, reverse=True)[
        : config.TOP_FILES
    ]
    top_linhas = sorted(arquivos, key=lambda item: item.total_changed, reverse=True)[
        : config.TOP_FILES
    ]
    extensoes = [
        ExtensionStats(
            extension=ext,
            commit_count=dados["commits"],
            total_changed=dados["changed"],
        )
        for ext, dados in por_extensao.items()
    ]
    extensoes.sort(key=lambda item: item.total_changed, reverse=True)

    cruzado = [
        FileAuthorCross(
            path=caminho,
            author_email=email,
            author_name=nome,
            commit_count=qtd,
        )
        for (caminho, email, nome), qtd in cruzamento.most_common(100)
    ]

    dono_unico = [arquivo for arquivo in arquivos if arquivo.author_count == 1]
    dono_unico.sort(key=lambda item: item.commit_count, reverse=True)

    return FileHotspotStats(
        top_by_commits=top_commits,
        top_by_lines=top_linhas,
        by_extension=extensoes,
        file_author_cross=cruzado,
        single_owner_files=dono_unico[: config.TOP_FILES],
        single_owner_count=len(dono_unico),
    )


def _normalizar_mensagem(texto: str) -> str:
    return _PONTUACAO_RE.sub("", texto.lower()).strip()


def _pontos_de_atencao(commits: list[Commit]) -> list[AttentionFlag]:
    flags: list[AttentionFlag] = []

    curtas = [
        commit
        for commit in commits
        if len(commit.message_summary.strip()) < config.SHORT_MESSAGE_CHARS
    ]
    if curtas:
        flags.append(
            AttentionFlag(
                kind="mensagem_curta",
                message=(
                    f"{len(curtas)} commit(s) com mensagem vazia ou com menos de "
                    f"{config.SHORT_MESSAGE_CHARS} caracteres."
                ),
                details=", ".join(c.sha_short for c in curtas[:8]),
            )
        )

    enormes = []
    for commit in commits:
        ins, dele = _linhas(commit)
        if ins + dele >= config.HUGE_COMMIT_LINES:
            enormes.append(commit)
    if enormes:
        flags.append(
            AttentionFlag(
                kind="commit_enorme",
                message=(
                    f"{len(enormes)} commit(s) alteram {config.HUGE_COMMIT_LINES} "
                    "linhas ou mais de uma vez — possível trabalho acumulado."
                ),
                details=", ".join(c.sha_short for c in enormes[:8]),
            )
        )

    repetidas: dict[str, list[Commit]] = defaultdict(list)
    for commit in commits:
        chave = _normalizar_mensagem(commit.message_summary)
        if chave:
            repetidas[chave].append(commit)
    genericas = [
        (chave, grupo)
        for chave, grupo in repetidas.items()
        if len(grupo) >= config.REPEATED_MESSAGE_MIN
    ]
    genericas.sort(key=lambda item: len(item[1]), reverse=True)
    for chave, grupo in genericas[:5]:
        flags.append(
            AttentionFlag(
                kind="mensagem_repetida",
                message=(
                    f'A mensagem "{grupo[0].message_summary.strip()}" aparece '
                    f"{len(grupo)} vezes."
                ),
                details=chave,
            )
        )

    por_email: dict[str, list[Commit]] = defaultdict(list)
    for commit in commits:
        por_email[commit.author_email].append(commit)
    for email, grupo in por_email.items():
        if len(grupo) < 2:
            continue
        dias = {commit.committed_at.date() for commit in grupo}
        if len(dias) == 1:
            nome = grupo[0].author_name
            flags.append(
                AttentionFlag(
                    kind="concentracao_temporal",
                    message=(
                        f"Todos os {len(grupo)} commits de {nome} ({email}) "
                        f"ocorreram no mesmo dia ({next(iter(dias)).isoformat()})."
                    ),
                    details=email,
                )
            )

    if len(commits) >= 2:
        inicio = min(commit.committed_at for commit in commits)
        fim = max(commit.committed_at for commit in commits)
        if fim - inicio >= timedelta(hours=config.LAST_WINDOW_HOURS * 2):
            janela = _janela_final(commits, config.LAST_WINDOW_HOURS)
            pct = _percentual(len(janela), len(commits))
            if pct >= config.LAST_WINDOW_RUSH_THRESHOLD_PCT:
                flags.append(
                    AttentionFlag(
                        kind="corrida_final",
                        message=(
                            f"{len(janela)} commit(s) ({pct}%) ocorreram nas últimas "
                            f"{config.LAST_WINDOW_HOURS}h do histórico — possível "
                            "corrida de última hora."
                        ),
                        details=", ".join(c.sha_short for c in janela[:8]),
                    )
                )

    reverts = [
        commit
        for commit in commits
        if commit.cc_type == "revert"
        or (commit.is_merge and "revert" in commit.message_summary.lower())
    ]
    if reverts:
        flags.append(
            AttentionFlag(
                kind="revert",
                message=f"{len(reverts)} revert(s) ou merge(s) de reversão encontrados.",
                details=", ".join(c.sha_short for c in reverts[:8]),
            )
        )

    return flags
