"""
Pipeline oficial das tabelas de produtos.

Este arquivo define a ordem suportada em substituição ao fluxo antigo:
1. produtos_unidades
2. produtos
3. produtos_agrupados + produtos_final
4. fatores_conversao
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from rich import print as rprint

from produtos_unidades import gerar_produtos_unidades
from produtos import gerar_tabela_produtos
from produtos_agrupados import gerar_produtos_agrupados
from fatores_conversao import gerar_fatores_conversao

TABELAS_OFICIAIS_PRODUTOS = [
    "produtos_unidades",
    "produtos",
    "produtos_agrupados",
    "produtos_final",
    "fatores_conversao",
]

TABELAS_LEGADAS_SUBSTITUIDAS = {
    "tabela_itens_caracteristicas": "produtos_unidades",
    "tabela_descricoes": "produtos",
    "tabela_codigos_mais_descricoes": "produtos_agrupados/produtos_final",
    "fator_conversao": "fatores_conversao",
}


def executar_pipeline_produtos(
    cnpj: str,
    pasta_cnpj: Path | None = None,
    agrupamentos_manuais: dict[str, list[str]] | None = None,
) -> bool:
    cnpj = re.sub(r"[^0-9]", "", str(cnpj))
    rprint(f"[bold cyan]Executando pipeline oficial de produtos para {cnpj}[/bold cyan]")

    if gerar_produtos_unidades(cnpj, pasta_cnpj) is None:
        return False
    if gerar_tabela_produtos(cnpj, pasta_cnpj) is None:
        return False
    if gerar_produtos_agrupados(cnpj, pasta_cnpj, agrupamentos_manuais) is None:
        return False
    if gerar_fatores_conversao(cnpj, pasta_cnpj) is None:
        rprint("[yellow]Pipeline finalizado sem fatores automáticos válidos.[/yellow]")
        return True
    return True


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print("Uso: python pipeline_produtos.py <cnpj>")
        raise SystemExit(1)
    raise SystemExit(0 if executar_pipeline_produtos(sys.argv[1]) else 1)
