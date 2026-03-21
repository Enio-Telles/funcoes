from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Callable

from rich import print as rprint


def sanitize_cnpj_cli(cnpj: str) -> str:
    return re.sub(r"[^0-9]", "", str(cnpj))


def validar_cnpj_basico(cnpj: str) -> bool:
    return len(sanitize_cnpj_cli(cnpj)) == 14


def executar_wrapper_legado(
    *,
    nome_legado: str,
    nome_novo: str,
    gerador: Callable[[str, Path | None], object],
    cnpj: str,
    pasta_cnpj: Path | None = None,
) -> bool:
    rprint(f"[yellow]{nome_legado} foi descontinuado. Gerando {nome_novo}.[/yellow]")
    return gerador(cnpj, pasta_cnpj) is not None


def main_wrapper_legado(
    *,
    nome_legado: str,
    nome_novo: str,
    gerador: Callable[[str, Path | None], object],
) -> int:
    cnpj_arg = sys.argv[1] if len(sys.argv) > 1 else input("Informe o CNPJ: ").strip()
    cnpj_arg = sanitize_cnpj_cli(cnpj_arg)
    if not validar_cnpj_basico(cnpj_arg):
        rprint(f"[red]CNPJ inválido: {cnpj_arg}[/red]")
        return 1
    return 0 if executar_wrapper_legado(nome_legado=nome_legado, nome_novo=nome_novo, gerador=gerador, cnpj=cnpj_arg) else 1
