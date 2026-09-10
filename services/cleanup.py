"""Remoção do clone temporário — sempre segura de chamar."""

from __future__ import annotations

import shutil
from pathlib import Path


def cleanup_repo(tmp_dir: str | Path | None) -> None:
    if not tmp_dir:
        return
    shutil.rmtree(tmp_dir, ignore_errors=True)
