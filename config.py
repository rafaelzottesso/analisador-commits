"""Limites e parâmetros ajustáveis do analisador."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

CLONE_TIMEOUT_SECONDS = 60
PIPELINE_TIMEOUT_SECONDS = 90
MAX_REPO_SIZE_MB = 200
MAX_COMMITS = 5000
TOP_FILES = 15
SHORT_MESSAGE_CHARS = 10
HUGE_COMMIT_LINES = 500
REPEATED_MESSAGE_MIN = 3
PARTICIPATION_BASE_PCT = 10.0

# gettempdir() em vez de /tmp fixo: os testes e o dev local no Windows
# precisam do diretório temporário do SO; no Cloud Run continua sendo /tmp.
TEMP_BASE_DIR = Path(
    os.environ.get("COMMIT_ANALYZER_TMP", Path(tempfile.gettempdir()) / "commit_analyzer")
)
GITHUB_API_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_API_TIMEOUT_SECONDS = 10


def participation_threshold_pct(n_authors: int) -> float:
    """Limiar de baixa participação: 10% dividido pelo número de autores."""
    if n_authors <= 0:
        return 0.0
    return PARTICIPATION_BASE_PCT / n_authors
