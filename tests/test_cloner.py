from pathlib import Path

from services.cleanup import cleanup_repo
from services.cloner import clone_repository
from tests.git_helpers import criar_repositorio_exemplo


def test_clone_repositorio_local(tmp_path: Path) -> None:
    origem = tmp_path / "origem"
    criar_repositorio_exemplo(origem)
    destino = clone_repository(str(origem))
    try:
        assert (destino / "HEAD").exists()
    finally:
        cleanup_repo(destino)


def test_cleanup_remove_diretorio(tmp_path: Path) -> None:
    pasta = tmp_path / "tmp-clone"
    pasta.mkdir()
    (pasta / "arquivo.txt").write_text("x", encoding="utf-8")
    cleanup_repo(pasta)
    assert not pasta.exists()


def test_cleanup_aceita_none() -> None:
    cleanup_repo(None)
