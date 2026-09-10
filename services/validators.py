"""Validação de URL do GitHub e checagem de tamanho via API."""

from __future__ import annotations

import json
import re
from datetime import date, datetime, time, timedelta, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import config
from models.commit import GitHubRepo
from services.errors import (
    AnalyzerError,
    CloneError,
    InvalidDateError,
    InvalidUrlError,
    NotGitHubError,
    RepoTooLargeError,
)


_GITHUB_REPO_RE = re.compile(
    r"^https://github\.com/"
    r"(?P<owner>[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38})/"
    r"(?P<repo>[A-Za-z0-9._-]+?)"
    r"(?:\.git)?/?$"
)

_MSG_NAO_GITHUB = "Por enquanto, só repositórios do GitHub são suportados."
_MSG_URL_INVALIDA = (
    "URL inválida. Use o formato https://github.com/usuario/repositorio"
)


def parse_github_url(url: str) -> GitHubRepo:
    """Valida só o formato — sem rede — e devolve owner/repo canônicos."""
    texto = url.strip()
    if not texto:
        raise InvalidUrlError(_MSG_URL_INVALIDA)

    parsed = urlparse(texto)
    if parsed.scheme != "https" or parsed.hostname is None:
        if "github.com" not in texto.lower():
            raise NotGitHubError(_MSG_NAO_GITHUB)
        raise InvalidUrlError(_MSG_URL_INVALIDA)

    host = parsed.hostname.lower()
    if host != "github.com":
        raise NotGitHubError(_MSG_NAO_GITHUB)

    if parsed.username or parsed.password or parsed.port:
        raise InvalidUrlError(_MSG_URL_INVALIDA)

    match = _GITHUB_REPO_RE.match(texto.rstrip())
    if not match:
        raise InvalidUrlError(_MSG_URL_INVALIDA)

    owner = match.group("owner")
    name = match.group("repo")
    if name in {".", ".."}:
        raise InvalidUrlError(_MSG_URL_INVALIDA)

    return GitHubRepo(
        owner=owner,
        name=name,
        canonical_url=f"https://github.com/{owner}/{name}.git",
    )


def check_repo_size(repo: GitHubRepo) -> int:
    """Consulta a API pública e recusa repositórios acima do limite (MB).

    O campo `size` da API do GitHub vem em KB.
    """
    api_url = f"https://api.github.com/repos/{repo.owner}/{repo.name}"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "analisador-commits",
    }
    if config.GITHUB_API_TOKEN:
        headers["Authorization"] = f"Bearer {config.GITHUB_API_TOKEN}"

    request = Request(api_url, headers=headers)
    try:
        with urlopen(request, timeout=config.GITHUB_API_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code in {401, 403, 404}:
            raise CloneError(
                "Não foi possível acessar este repositório. "
                "Verifique se a URL está correta e se o repositório é público."
            ) from exc
        raise
    except (URLError, TimeoutError) as exc:
        # TimeoutError "puro" acontece quando o timeout estoura durante a
        # leitura da resposta (h.getresponse()): urllib só converte para
        # URLError os erros no envio da requisição, não na leitura.
        raise CloneError(
            "Não foi possível acessar este repositório. "
            "Verifique se a URL está correta e se o repositório é público."
        ) from exc

    size_kb = int(payload.get("size") or 0)
    size_mb = size_kb / 1024
    if size_mb > config.MAX_REPO_SIZE_MB:
        raise RepoTooLargeError(
            "Este repositório é muito grande para ser analisado "
            f"(limite atual: {config.MAX_REPO_SIZE_MB} MB)."
        )
    return size_kb


FUSO_SP = timezone(timedelta(hours=-3))


def parse_date_filters(
    date_1_raw: str | None,
    date_2_raw: str | None,
) -> tuple[datetime | None, datetime | None]:
    """Valida e converte datas opcionais para o fim do dia (23:59:59.999999 UTC-3)."""
    d1_texto = (date_1_raw or "").strip()
    d2_texto = (date_2_raw or "").strip()

    if not d1_texto and d2_texto:
        raise InvalidDateError(
            "Para informar a Data 2 (segunda entrega), é obrigatório informar a Data 1."
        )

    dt_1 = _parse_single_date(d1_texto, "Data 1") if d1_texto else None
    dt_2 = _parse_single_date(d2_texto, "Data 2") if d2_texto else None

    if dt_1 and dt_2 and dt_2 <= dt_1:
        raise InvalidDateError("A Data 2 (segunda entrega) deve ser posterior à Data 1.")

    return dt_1, dt_2


def _parse_single_date(valor: str, campo: str) -> datetime:
    try:
        data = date.fromisoformat(valor)
    except ValueError as exc:
        raise InvalidDateError(
            f"{campo} inválida. Utilize uma data válida no formato AAAA-MM-DD."
        ) from exc
    return datetime.combine(data, time.max, tzinfo=FUSO_SP)

