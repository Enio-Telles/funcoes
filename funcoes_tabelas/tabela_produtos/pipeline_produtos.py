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
    "tabela_codigos_mais_descricoes": "produtos_agrupados",
    "fator_conversao": "fatores_conversao",
}

DEPENDENCIAS = {
    "produtos_unidades": [],
    "produtos": ["produtos_unidades"],
    "produtos_agrupados": ["produtos", "produtos_unidades"],
    "produtos_final": ["produtos_agrupados"],
    "fatores_conversao": ["produtos_final", "produtos", "produtos_unidades"],
}


def _expandir_dependencias(selecionadas: list[str] | None) -> list[str]:
    if not selecionadas:
        return TABELAS_OFICIAIS_PRODUTOS[:]

    normalizadas = []
    for tab in selecionadas:
        destino = TABELAS_LEGADAS_SUBSTITUIDAS.get(tab, tab)
        if destino == "produtos_agrupados/produtos_final":
            for t in ["produtos_agrupados", "produtos_final"]:
                if t not in normalizadas:
                    normalizadas.append(t)
        elif destino not in normalizadas:
            normalizadas.append(destino)

    expandidas = set()

    def add(tab: str):
        if tab in expandidas:
            return
        for dep in DEPENDENCIAS.get(tab, []):
            add(dep)
        expandidas.add(tab)
        if tab == "produtos_agrupados":
            expandidas.add("produtos_final")

    for tab in normalizadas:
        add(tab)

    return [t for t in TABELAS_OFICIAIS_PRODUTOS if t in expandidas]


def executar_pipeline_produtos(
    cnpj: str,
    pasta_cnpj: Path | None = None,
    agrupamentos_manuais: dict[str, list[str]] | None = None,
    tabelas_selecionadas: list[str] | None = None,
) -> list[str]:
    cnpj = re.sub(r"[^0-9]", "", str(cnpj))
    ordem = _expandir_dependencias(tabelas_selecionadas)
    rprint(f"[bold cyan]Executando pipeline oficial de produtos para {cnpj}[/bold cyan]")
    rprint(f"[cyan]Etapas: {', '.join(ordem)}[/cyan]")

    geradas: list[str] = []

    if "produtos_unidades" in ordem:
        if gerar_produtos_unidades(cnpj, pasta_cnpj) is None:
            return []
        geradas.append("produtos_unidades")

    if "produtos" in ordem:
        if gerar_tabela_produtos(cnpj, pasta_cnpj) is None:
            return geradas
        geradas.append("produtos")

    if "produtos_agrupados" in ordem or "produtos_final" in ordem:
        if gerar_produtos_agrupados(cnpj, pasta_cnpj, agrupamentos_manuais) is None:
            return geradas
        if "produtos_agrupados" in ordem:
            geradas.append("produtos_agrupados")
        if "produtos_final" in ordem:
            geradas.append("produtos_final")

    if "fatores_conversao" in ordem:
        fatores = gerar_fatores_conversao(cnpj, pasta_cnpj)
        if fatores is None:
            rprint("[yellow]Pipeline finalizado sem fatores automáticos válidos.[/yellow]")
        else:
            geradas.append("fatores_conversao")

    return geradas


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print("Uso: python pipeline_produtos.py <cnpj>")
        raise SystemExit(1)
    raise SystemExit(0 if executar_pipeline_produtos(sys.argv[1]) else 1)
