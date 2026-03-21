"""
Compatibilidade legada.

A antiga tabela_descricoes foi substituída por produtos.
"""

from __future__ import annotations

from pathlib import Path

from produtos import gerar_tabela_produtos
from _legacy_wrapper import executar_wrapper_legado, main_wrapper_legado


def gerar_tabela_descricoes(cnpj: str, pasta_cnpj: Path | None = None) -> bool:
    return executar_wrapper_legado(
        nome_legado="tabela_descricoes",
        nome_novo="produtos",
        gerador=gerar_tabela_produtos,
        cnpj=cnpj,
        pasta_cnpj=pasta_cnpj,
    )


if __name__ == "__main__":
    raise SystemExit(
        main_wrapper_legado(
            nome_legado="tabela_descricoes",
            nome_novo="produtos",
            gerador=gerar_tabela_produtos,
        )
    )
