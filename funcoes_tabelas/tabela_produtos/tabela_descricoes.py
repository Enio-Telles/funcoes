"""
Compatibilidade legada.

A antiga tabela_descricoes foi substituída por produtos.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from rich import print as rprint

from produtos import gerar_tabela_produtos

try:
    from validar_cnpj import validar_cnpj
except ImportError:
    def validar_cnpj(cnpj: str) -> bool:
        return len(re.sub(r"[^0-9]", "", str(cnpj))) == 14


def gerar_tabela_descricoes(cnpj: str, pasta_cnpj: Path | None = None) -> bool:
    rprint("[yellow]tabela_descricoes foi descontinuada. Gerando produtos.[/yellow]")
    return gerar_tabela_produtos(cnpj, pasta_cnpj) is not None


if __name__ == "__main__":
    cnpj_arg = sys.argv[1] if len(sys.argv) > 1 else input("Informe o CNPJ: ").strip()
    cnpj_arg = re.sub(r"[^0-9]", "", cnpj_arg)
    if not validar_cnpj(cnpj_arg):
        rprint(f"[red]CNPJ inválido: {cnpj_arg}[/red]")
        sys.exit(1)
    sys.exit(0 if gerar_tabela_descricoes(cnpj_arg) else 1)
