"""Agregações do relatório a partir da lista de Commit já enriquecida."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import config
from models.commit import (
    AttentionFlag,
    AuthorCount,
    AuthorStats,
    AuthorTypeCount,
    Commit,
    CommitTypeStats,
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
        commit_types=_tipos(commits),
        timeline=_linha_do_tempo(commits),
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


def _resumo(commits: list[Commit], limitado: bool) -> SummaryStats:
    emails = {commit.author_email for commit in commits}
    insercoes = remocoes = 0
    merges = 0
    conventional = 0
    for commit in commits:
        ins, dele = _linhas(commit)
        insercoes += ins
        remocoes += dele
        if commit.is_merge:
            merges += 1
        if commit.is_conventional:
            conventional += 1

    datas = [commit.committed_at for commit in commits]
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
    )


def _autores(commits: list[Commit]) -> list[AuthorStats]:
    por_email: dict[str, list[Commit]] = defaultdict(list)
    for commit in commits:
        por_email[commit.author_email].append(commit)

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
            )
        )

    resultado.sort(key=lambda autor: autor.commit_count, reverse=True)
    return resultado


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

    inicio = min(commit.committed_at.date() for commit in commits)
    fim = max(commit.committed_at.date() for commit in commits)
    calendario = pd.date_range(inicio, fim, freq="D")
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
    return FileHotspotStats(
        top_by_commits=top_commits,
        top_by_lines=top_linhas,
        by_extension=extensoes,
        file_author_cross=cruzado,
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
