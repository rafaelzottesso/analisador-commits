"""Formatação de números no padrão brasileiro (pt-BR) — sem depender de locale do SO."""

from __future__ import annotations


def format_number(valor: int | float | None, casas: int | None = None) -> str:
    """Ponto como separador de milhar e vírgula como decimal: 12345.6 -> "12.345,6".

    Inteiros saem sem casas decimais; floats usam 1 casa por padrão (as
    porcentagens do relatório já vêm arredondadas a 1 casa).
    """
    if valor is None:
        return ""
    if casas is None:
        casas = 0 if isinstance(valor, int) else 1
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "\x00").replace(".", ",").replace("\x00", ".")
