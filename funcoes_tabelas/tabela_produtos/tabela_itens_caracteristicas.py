"""
Compatibilidade legada.

A antiga tabela_itens_caracteristicas foi substituída por produtos_unidades.
Este módulo mantém a assinatura antiga, mas gera apenas as novas tabelas.
"""

from __future__ import annotations

from pathlib import Path

from produtos_unidades import gerar_produtos_unidades
from _legacy_wrapper import executar_wrapper_legado, main_wrapper_legado


def gerar_tabela_itens_caracteristicas(cnpj: str, pasta_cnpj: Path | None = None) -> bool:
    return executar_wrapper_legado(
        nome_legado="tabela_itens_caracteristicas",
        nome_novo="produtos_unidades",
        gerador=gerar_produtos_unidades,
        cnpj=cnpj,
        pasta_cnpj=pasta_cnpj,
    )


if __name__ == "__main__":
    raise SystemExit(
        main_wrapper_legado(
            nome_legado="tabela_itens_caracteristicas",
            nome_novo="produtos_unidades",
            gerador=gerar_produtos_unidades,
        )
    )
