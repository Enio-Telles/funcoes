"""
Compatibilidade legada.

A antiga tabela_codigos_mais_descricoes foi substituída por produtos_agrupados + produtos_final.
"""

from __future__ import annotations

from pathlib import Path

from produtos_agrupados import gerar_produtos_agrupados
from _legacy_wrapper import executar_wrapper_legado, main_wrapper_legado


def tabela_codigos_mais_descricoes(cnpj: str, pasta_cnpj: Path | None = None) -> bool:
    return executar_wrapper_legado(
        nome_legado="tabela_codigos_mais_descricoes",
        nome_novo="produtos_agrupados e produtos_final",
        gerador=gerar_produtos_agrupados,
        cnpj=cnpj,
        pasta_cnpj=pasta_cnpj,
    )


if __name__ == "__main__":
    raise SystemExit(
        main_wrapper_legado(
            nome_legado="tabela_codigos_mais_descricoes",
            nome_novo="produtos_agrupados e produtos_final",
            gerador=gerar_produtos_agrupados,
        )
    )
