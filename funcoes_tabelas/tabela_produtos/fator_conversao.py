"""
Compatibilidade legada.

O antigo fator_conversao foi substituído por fatores_conversao.
"""

from __future__ import annotations

from pathlib import Path

from fatores_conversao import gerar_fatores_conversao
from _legacy_wrapper import executar_wrapper_legado, main_wrapper_legado


def calcular_fator_conversao(cnpj: str, pasta_cnpj: Path | None = None) -> bool:
    return executar_wrapper_legado(
        nome_legado="fator_conversao",
        nome_novo="fatores_conversao",
        gerador=gerar_fatores_conversao,
        cnpj=cnpj,
        pasta_cnpj=pasta_cnpj,
    )


if __name__ == "__main__":
    raise SystemExit(
        main_wrapper_legado(
            nome_legado="fator_conversao",
            nome_novo="fatores_conversao",
            gerador=gerar_fatores_conversao,
        )
    )
