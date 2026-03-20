"""
Compatibilidade legada.

A antiga tabela_itens_caracteristicas foi substituída por produtos_unidades.
Este módulo mantém a assinatura antiga, mas gera apenas as novas tabelas.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from rich import print as rprint

from produtos_unidades import gerar_produtos_unidades

try:
    from validar_cnpj import validar_cnpj
except ImportError:
    def validar_cnpj(cnpj: str) -> bool:
        return len(re.sub(r"[^0-9]", "", str(cnpj))) == 14


def gerar_tabela_itens_caracteristicas(cnpj: str, pasta_cnpj: Path | None = None) -> bool:
    rprint("[yellow]tabela_itens_caracteristicas foi descontinuada. Gerando produtos_unidades.[/yellow]")
    return gerar_produtos_unidades(cnpj, pasta_cnpj) is not None


if __name__ == "__main__":
    cnpj_arg = sys.argv[1] if len(sys.argv) > 1 else input("Informe o CNPJ: ").strip()
    cnpj_arg = re.sub(r"[^0-9]", "", cnpj_arg)
    if not validar_cnpj(cnpj_arg):
        rprint(f"[red]CNPJ inválido: {cnpj_arg}[/red]")
        sys.exit(1)
    sys.exit(0 if gerar_tabela_itens_caracteristicas(cnpj_arg) else 1)
