from services.formatting import format_number


def test_inteiro_com_milhar() -> None:
    assert format_number(5000) == "5.000"
    assert format_number(1234567) == "1.234.567"


def test_inteiro_pequeno_e_negativo() -> None:
    assert format_number(42) == "42"
    assert format_number(-1500) == "-1.500"


def test_float_usa_virgula_decimal() -> None:
    assert format_number(66.7) == "66,7"
    assert format_number(0.0) == "0,0"
    assert format_number(12345.6) == "12.345,6"


def test_casas_explicitas() -> None:
    assert format_number(3.14159, casas=2) == "3,14"
    assert format_number(1500.0, casas=0) == "1.500"


def test_none_vira_vazio() -> None:
    assert format_number(None) == ""
