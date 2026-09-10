"""Clone bare em diretório temporário, com timeout e sem shell=True."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

import config
from services.errors import CloneError, CloneTimeoutError

_MSG_CLONE = (
    "Não foi possível acessar este repositório. "
    "Verifique se a URL está correta e se o repositório é público."
)
_MSG_TIMEOUT = (
    "O repositório demorou muito para ser clonado. "
    "Tente novamente ou use um repositório menor."
)


def clone_repository(url: str) -> Path:
    config.TEMP_BASE_DIR.mkdir(parents=True, exist_ok=True)
    tmp_dir = Path(tempfile.mkdtemp(prefix="repo-", dir=config.TEMP_BASE_DIR))
    # Sem --filter=blob:none: o extractor precisa do diff completo de cada
    # commit, então um clone parcial só adiaria o custo para buscas de blob
    # sob demanda (uma por objeto faltante) durante a extração — mais lento
    # no total do que baixar tudo de uma vez aqui.
    comando = [
        "git",
        "clone",
        "--bare",
        "--single-branch",
        url,
        str(tmp_dir),
    ]
    try:
        resultado = subprocess.run(
            comando,
            timeout=config.CLONE_TIMEOUT_SECONDS,
            check=False,
            capture_output=True,
            text=True,
        )
    except subprocess.TimeoutExpired as exc:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise CloneTimeoutError(_MSG_TIMEOUT) from exc

    if resultado.returncode != 0:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise CloneError(_MSG_CLONE)
    return tmp_dir
