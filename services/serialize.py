"""Converte dataclasses do relatório em estruturas aceitas por JSON/Jinja."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from datetime import datetime
from typing import Any


def to_jsonable(obj: Any) -> Any:
    if is_dataclass(obj) and not isinstance(obj, type):
        return {campo.name: to_jsonable(getattr(obj, campo.name)) for campo in fields(obj)}
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, list):
        return [to_jsonable(item) for item in obj]
    if isinstance(obj, dict):
        return {str(chave): to_jsonable(valor) for chave, valor in obj.items()}
    return obj
