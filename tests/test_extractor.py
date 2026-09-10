from pathlib import Path

import pytest

from services.cleanup import cleanup_repo
from services.cloner import clone_repository
from services.errors import EmptyRepositoryError
from services.extractor import extract_commits
from tests.git_helpers import criar_repositorio_exemplo, init_repo


def test_extrai_commits_conventional_e_nao(tmp_path: Path) -> None:
    origem = tmp_path / "origem"
    criar_repositorio_exemplo(origem)
    clone = clone_repository(str(origem))
    try:
        commits, limitado = extract_commits(clone)
    finally:
        cleanup_repo(clone)

    assert limitado is False
    assert len(commits) == 3
    tipos = {c.cc_type for c in commits if c.is_conventional}
    assert "feat" in tipos
    assert "fix" in tipos
    assert any(not c.is_conventional for c in commits)
    emails = {c.author_email for c in commits}
    assert emails == {"ana@example.com", "bruno@example.com"}
    assert any(c.files_changed for c in commits)


def test_respeita_limite_de_commits(tmp_path: Path) -> None:
    origem = tmp_path / "origem"
    criar_repositorio_exemplo(origem)
    clone = clone_repository(str(origem))
    try:
        commits, limitado = extract_commits(clone, max_commits=2)
    finally:
        cleanup_repo(clone)
    assert len(commits) == 2
    assert limitado is True


def test_repositorio_vazio_levanta_erro(tmp_path: Path) -> None:
    origem = tmp_path / "vazio"
    init_repo(origem)
    clone = clone_repository(str(origem))
    try:
        with pytest.raises(EmptyRepositoryError, match="não possui histórico"):
            extract_commits(clone)
    finally:
        cleanup_repo(clone)
