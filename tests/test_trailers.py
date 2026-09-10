from services.trailers import parse_coauthors


def test_sem_trailer() -> None:
    assert parse_coauthors("feat: adiciona login") == []


def test_um_coautor() -> None:
    mensagem = "feat: adiciona login\n\nCo-authored-by: Bruno Souza <bruno@example.com>"
    coautores = parse_coauthors(mensagem)
    assert len(coautores) == 1
    assert coautores[0].name == "Bruno Souza"
    assert coautores[0].email == "bruno@example.com"


def test_varios_coautores() -> None:
    mensagem = (
        "fix: corrige bug\n\n"
        "Co-authored-by: Bruno Souza <bruno@example.com>\n"
        "Co-authored-by: Carla Lima <carla@example.com>"
    )
    coautores = parse_coauthors(mensagem)
    emails = {c.email for c in coautores}
    assert emails == {"bruno@example.com", "carla@example.com"}


def test_email_duplicado_conta_uma_vez() -> None:
    mensagem = (
        "fix: corrige bug\n\n"
        "Co-authored-by: Bruno Souza <bruno@example.com>\n"
        "Co-authored-by: Bruno <bruno@example.com>"
    )
    coautores = parse_coauthors(mensagem)
    assert len(coautores) == 1


def test_case_insensitive() -> None:
    mensagem = "fix: x\n\nco-Authored-By: Bruno Souza <bruno@example.com>"
    coautores = parse_coauthors(mensagem)
    assert len(coautores) == 1
