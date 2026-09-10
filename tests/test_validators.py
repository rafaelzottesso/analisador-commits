from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

import pytest

import config
from services.errors import CloneError, InvalidUrlError, NotGitHubError, RepoTooLargeError
from services.validators import check_repo_size, parse_github_url


class TestParseGithubUrl:
    def test_url_simples(self) -> None:
        repo = parse_github_url("https://github.com/owner/repo")
        assert repo.owner == "owner"
        assert repo.name == "repo"
        assert repo.canonical_url == "https://github.com/owner/repo.git"

    def test_com_git_e_barra_final(self) -> None:
        repo = parse_github_url("https://github.com/owner/repo.git/")
        assert repo.name == "repo"
        assert repo.canonical_url == "https://github.com/owner/repo.git"

    def test_com_espacos_nas_bordas(self) -> None:
        repo = parse_github_url("  https://github.com/IFPR/aula-web  ")
        assert repo.owner == "IFPR"
        assert repo.name == "aula-web"

    def test_ssh_nao_aceito(self) -> None:
        with pytest.raises(InvalidUrlError, match="URL inválida"):
            parse_github_url("git@github.com:owner/repo.git")

    def test_outro_host(self) -> None:
        with pytest.raises(NotGitHubError):
            parse_github_url("https://gitlab.com/owner/repo")

    def test_host_parece_github_mas_nao_e(self) -> None:
        with pytest.raises(NotGitHubError):
            parse_github_url("https://github.com.evil.com/owner/repo")

    def test_sem_repositorio(self) -> None:
        with pytest.raises(InvalidUrlError, match="URL inválida"):
            parse_github_url("https://github.com/owner")

    def test_caminho_extra(self) -> None:
        with pytest.raises(InvalidUrlError):
            parse_github_url("https://github.com/owner/repo/issues")

    def test_vazio(self) -> None:
        with pytest.raises(InvalidUrlError):
            parse_github_url("")

    def test_http_simples(self) -> None:
        with pytest.raises(InvalidUrlError):
            parse_github_url("http://github.com/owner/repo")


class TestCheckRepoSize:
    def test_dentro_do_limite(self) -> None:
        repo = parse_github_url("https://github.com/owner/repo")
        payload = MagicMock()
        payload.read.return_value = b'{"size": 1024}'
        payload.__enter__.return_value = payload
        payload.__exit__.return_value = False
        with patch("services.validators.urlopen", return_value=payload):
            size_kb = check_repo_size(repo)
        assert size_kb == 1024

    def test_acima_do_limite(self) -> None:
        repo = parse_github_url("https://github.com/owner/repo")
        tamanho_kb = (config.MAX_REPO_SIZE_MB + 1) * 1024
        payload = MagicMock()
        payload.read.return_value = f'{{"size": {tamanho_kb}}}'.encode()
        payload.__enter__.return_value = payload
        payload.__exit__.return_value = False
        with patch("services.validators.urlopen", return_value=payload):
            with pytest.raises(RepoTooLargeError, match="muito grande"):
                check_repo_size(repo)

    def test_nao_encontrado(self) -> None:
        repo = parse_github_url("https://github.com/owner/repo")
        error = HTTPError(
            url="https://api.github.com/repos/owner/repo",
            code=404,
            msg="Not Found",
            hdrs=None,
            fp=None,
        )
        with patch("services.validators.urlopen", side_effect=error):
            with pytest.raises(CloneError, match="Não foi possível acessar"):
                check_repo_size(repo)

    def test_timeout_na_leitura_da_resposta(self) -> None:
        """urllib não envolve em URLError o timeout que estoura em getresponse()."""
        repo = parse_github_url("https://github.com/owner/repo")
        with patch("services.validators.urlopen", side_effect=TimeoutError("timed out")):
            with pytest.raises(CloneError, match="Não foi possível acessar"):
                check_repo_size(repo)


class TestParseDateFilters:
    def test_sem_datas(self) -> None:
        from services.validators import parse_date_filters
        d1, d2 = parse_date_filters(None, None)
        assert d1 is None
        assert d2 is None

    def test_apenas_data_1(self) -> None:
        from services.validators import parse_date_filters
        d1, d2 = parse_date_filters("2024-03-15", "")
        assert d1 is not None
        assert d2 is None
        assert d1.year == 2024 and d1.month == 3 and d1.day == 15
        assert d1.hour == 23 and d1.minute == 59 and d1.second == 59

    def test_duas_datas_validas(self) -> None:
        from services.validators import parse_date_filters
        d1, d2 = parse_date_filters("2024-03-15", "2024-03-30")
        assert d1 is not None
        assert d2 is not None
        assert d2 > d1
        assert d2.day == 30

    def test_apenas_data_2_sem_data_1(self) -> None:
        from services.errors import InvalidDateError
        from services.validators import parse_date_filters
        with pytest.raises(InvalidDateError, match="obrigatório informar a Data 1"):
            parse_date_filters("", "2024-03-30")

    def test_data_2_igual_ou_anterior_data_1(self) -> None:
        from services.errors import InvalidDateError
        from services.validators import parse_date_filters
        with pytest.raises(InvalidDateError, match="deve ser posterior à Data 1"):
            parse_date_filters("2024-03-15", "2024-03-15")

        with pytest.raises(InvalidDateError, match="deve ser posterior à Data 1"):
            parse_date_filters("2024-03-20", "2024-03-15")

    def test_formato_invalido(self) -> None:
        from services.errors import InvalidDateError
        from services.validators import parse_date_filters
        with pytest.raises(InvalidDateError, match="inválida"):
            parse_date_filters("15/03/2024", None)

