"""
Compatibilidade legada.

O antigo fator_conversao foi substituído por fatores_conversao.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from rich import print as rprint

from fatores_conversao import gerar_fatores_conversao

try:
    from validar_cnpj import validar_cnpj
except ImportError:
    def validar_cnpj(cnpj: str) -> bool:
        return len(re.sub(r"[^0-9]", "", str(cnpj))) == 14


def calcular_fator_conversao(cnpj: str, pasta_cnpj: Path | None = None) -> bool:
    rprint("[yellow]fator_conversao foi descontinuado. Gerando fatores_conversao.[/yellow]")
    return gerar_fatores_conversao(cnpj, pasta_cnpj) is not None


if __name__ == "__main__":
    cnpj_arg = sys.argv[1] if len(sys.argv) > 1 else input("Informe o CNPJ: ").strip()
    cnpj_arg = re.sub(r"[^0-9]", "", cnpj_arg)
    if not validar_cnpj(cnpj_arg):
        rprint(f"[red]CNPJ inválido: {cnpj_arg}[/red]")
        sys.exit(1)
    sys.exit(0 if calcular_fator_conversao(cnpj_arg) else 1)
