from datetime import datetime, timezone

from models.commit import Commit
from services.conventional_commits import enrich_commit, parse_conventional_commit


def _commit(summary: str) -> Commit:
    return Commit(
        sha="a" * 40,
        sha_short="a" * 7,
        author_name="Ana",
        author_email="ana@example.com",
        committed_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        message=summary,
        message_summary=summary,
        is_merge=False,
    )


class TestParseConventionalCommit:
    def test_cada_tipo_valido_sem_escopo(self) -> None:
        tipos = (
            "feat",
            "fix",
            "docs",
            "style",
            "refactor",
            "perf",
            "test",
            "build",
            "ci",
            "chore",
            "revert",
        )
        for tipo in tipos:
            parsed = parse_conventional_commit(f"{tipo}: adiciona item")
            assert parsed.is_conventional is True
            assert parsed.cc_type == tipo
            assert parsed.cc_scope is None
            assert parsed.cc_description == "adiciona item"
            assert parsed.is_breaking is False

    def test_com_escopo(self) -> None:
        parsed = parse_conventional_commit("feat(auth): implementa login")
        assert parsed.is_conventional is True
        assert parsed.cc_type == "feat"
        assert parsed.cc_scope == "auth"
        assert parsed.cc_description == "implementa login"

    def test_escopo_com_hifen_e_barra(self) -> None:
        parsed = parse_conventional_commit("fix(api/v2): corrige rota")
        assert parsed.cc_scope == "api/v2"
        parsed = parse_conventional_commit("feat(user-auth): adiciona token")
        assert parsed.cc_scope == "user-auth"

    def test_breaking_change(self) -> None:
        parsed = parse_conventional_commit("feat(api)!: remove endpoint legado")
        assert parsed.is_conventional is True
        assert parsed.is_breaking is True
        assert parsed.cc_description == "remove endpoint legado"

    def test_nao_conventional(self) -> None:
        parsed = parse_conventional_commit("ajustes no formulário")
        assert parsed.is_conventional is False
        assert parsed.cc_type is None
        assert parsed.cc_scope is None
        assert parsed.cc_description is None

    def test_mensagem_vazia(self) -> None:
        parsed = parse_conventional_commit("")
        assert parsed.is_conventional is False
        parsed = parse_conventional_commit("   ")
        assert parsed.is_conventional is False

    def test_dois_pontos_no_meio_da_descricao(self) -> None:
        parsed = parse_conventional_commit("feat: add: something")
        assert parsed.is_conventional is True
        assert parsed.cc_description == "add: something"

    def test_tipo_maiusculo_nao_casa(self) -> None:
        parsed = parse_conventional_commit("FEAT: adiciona item")
        assert parsed.is_conventional is False

    def test_sem_espaco_apos_dois_pontos(self) -> None:
        parsed = parse_conventional_commit("feat:adiciona item")
        assert parsed.is_conventional is False

    def test_strip_nas_bordas(self) -> None:
        parsed = parse_conventional_commit("  fix(ui): corrige botão  ")
        assert parsed.is_conventional is True
        assert parsed.cc_type == "fix"

    def test_tipo_desconhecido(self) -> None:
        parsed = parse_conventional_commit("wip: trabalho em progresso")
        assert parsed.is_conventional is False


class TestEnrichCommit:
    def test_preenche_campos_conventional(self) -> None:
        commit = enrich_commit(_commit("docs(readme): atualiza instalação"))
        assert commit.is_conventional is True
        assert commit.cc_type == "docs"
        assert commit.cc_scope == "readme"
        assert commit.cc_description == "atualiza instalação"

    def test_nao_conventional_fica_nulo(self) -> None:
        commit = enrich_commit(_commit("fix"))
        assert commit.is_conventional is False
        assert commit.cc_type is None
