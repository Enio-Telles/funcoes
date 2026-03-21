from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

import polars as pl

FUNCOES_DIR = (
    Path(r"c:\funcoes")
    if Path(r"c:\funcoes").exists()
    else Path(__file__).resolve().parent.parent.parent.parent
)
AUXILIARES_DIR = FUNCOES_DIR / "funcoes_auxiliares"


def bootstrap_auxiliares_path() -> None:
    path = str(AUXILIARES_DIR)
    if path not in sys.path:
        sys.path.insert(0, path)


bootstrap_auxiliares_path()

try:
    from salvar_para_parquet import salvar_para_parquet as _salvar_para_parquet
except ImportError:
    def _salvar_para_parquet(df: pl.DataFrame, pasta: Path, nome: str) -> bool:
        pasta.mkdir(parents=True, exist_ok=True)
        df.write_parquet(pasta / nome)
        return True


def salvar_para_parquet(df: pl.DataFrame, pasta: Path, nome: str) -> bool:
    return _salvar_para_parquet(df, pasta, nome)


def sanitize_cnpj(cnpj: str) -> str:
    return re.sub(r"[^0-9]", "", str(cnpj))


def normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    value = unicodedata.normalize("NFD", str(value))
    value = "".join(c for c in value if unicodedata.category(c) != "Mn")
    return " ".join(value.upper().strip().split()) or None


def clean_code(value: str | None) -> str | None:
    text = normalize_text(value)
    if text is None:
        return None
    return text.lstrip("0") or "0"


def clean_punct_code(value: str | None) -> str | None:
    text = normalize_text(value)
    if text is None:
        return None
    return re.sub(r"[^0-9A-Z]", "", text) or None
