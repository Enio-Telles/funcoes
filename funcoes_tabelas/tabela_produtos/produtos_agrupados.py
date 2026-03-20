"""
Módulo: produtos_agrupados.py
Objetivo: permitir a união manual de linhas da tabela produtos em uma nova
Tabela produtos_agrupados e recalcular produtos_final.
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

import polars as pl
from rich import print as rprint

FUNCOES_DIR = (
    Path(r"c:\funcoes")
    if Path(r"c:\funcoes").exists()
    else Path(__file__).resolve().parent.parent.parent.parent
)
AUXILIARES_DIR = FUNCOES_DIR / "funcoes_auxiliares"

if str(AUXILIARES_DIR) not in sys.path:
    sys.path.insert(0, str(AUXILIARES_DIR))

try:
    from salvar_para_parquet import salvar_para_parquet
except ImportError:
    def salvar_para_parquet(df, pasta, nome):
        pasta.mkdir(parents=True, exist_ok=True)
        df.write_parquet(pasta / nome)
        return True


def _sanitizar_cnpj(cnpj: str) -> str:
    return re.sub(r"[^0-9]", "", str(cnpj))


def _limpos(lista: list[str] | None) -> list[str]:
    if not lista:
        return []
    return [str(x).strip() for x in lista if x not in (None, "", []) and str(x).strip()]


def _contar_campos_preenchidos(d: dict) -> int:
    return sum(1 for campo in ["lista_ncm", "lista_cest", "lista_gtin"] if _limpos(d.get(campo)))


def _moda_simples(lista: list[str] | None) -> str | None:
    valores = _limpos(lista)
    if not valores:
        return None
    cont = Counter(valores)
    maior = max(cont.values())
    candidatos = [k for k, v in cont.items() if v == maior]
    candidatos.sort(key=lambda x: (len(x), x), reverse=True)
    return candidatos[0]


def _co_sefin_divergente(lista: list[str] | None) -> bool:
    return len(set(_limpos(lista))) > 1


def _escolher_melhor_descricao(descricoes: list[str], dict_grupo: list[dict]) -> str | None:
    valores = _limpos(descricoes)
    if not valores:
        return None

    cont = Counter(valores)
    maior = max(cont.values())
    candidatos = [k for k, v in cont.items() if v == maior]
    if len(candidatos) == 1:
        return candidatos[0]

    candidatos_com_peso = []
    for cand in candidatos:
        reg = next((d for d in dict_grupo if d.get("descricao") == cand), None)
        peso = _contar_campos_preenchidos(reg or {})
        candidatos_com_peso.append((cand, peso))

    candidatos_com_peso.sort(key=lambda x: x[1], reverse=True)
    melhor_peso = candidatos_com_peso[0][1]
    empatados = [c for c, p in candidatos_com_peso if p == melhor_peso]
    empatados.sort(key=lambda x: len(x), reverse=True)
    return empatados[0]


def _agregar_registros(id_agrupado: str, chaves: list[str], dict_grupo: list[dict]) -> dict:
    todas_descricoes = [d.get("descricao") for d in dict_grupo]
    todos_ncms = [item for d in dict_grupo for item in _limpos(d.get("lista_ncm"))]
    todos_cests = [item for d in dict_grupo for item in _limpos(d.get("lista_cest"))]
    todos_gtins = [item for d in dict_grupo for item in _limpos(d.get("lista_gtin"))]
    todos_co_sefin = [item for d in dict_grupo for item in _limpos(d.get("lista_co_sefin"))]
    todas_unids = sorted(set(item for d in dict_grupo for item in _limpos(d.get("lista_unid"))))

    return {
        "id_agrupado": id_agrupado,
        "lista_chave_produto": sorted(set(chaves)),
        "descr_padrao": _escolher_melhor_descricao(todas_descricoes, dict_grupo),
        "ncm_padrao": _moda_simples(todos_ncms),
        "cest_padrao": _moda_simples(todos_cests),
        "gtin_padrao": _moda_simples(todos_gtins),
        "lista_co_sefin": sorted(set(todos_co_sefin)),
        "co_sefin_padrao": _moda_simples(todos_co_sefin),
        "lista_unidades": todas_unids,
        "co_sefin_divergentes": _co_sefin_divergente(todos_co_sefin),
    }


def gerar_produtos_agrupados(
    cnpj: str,
    pasta_cnpj: Path | None = None,
    agrupamentos_manuais: dict[str, list[str]] | None = None,
) -> pl.DataFrame | None:
    cnpj = _sanitizar_cnpj(cnpj)
    if pasta_cnpj is None:
        pasta_cnpj = FUNCOES_DIR / "CNPJ" / cnpj

    pasta_produtos = pasta_cnpj / "analises" / "produtos"
    arq_produtos = pasta_produtos / f"produtos_{cnpj}.parquet"
    if not arq_produtos.exists():
        rprint(f"[red]Erro: Tabela base {arq_produtos} não encontrada.[/red]")
        return None

    df_produtos = pl.read_parquet(arq_produtos)
    if df_produtos.is_empty():
        return None

    registros: list[dict] = []

    if not agrupamentos_manuais:
        for idx, d in enumerate(df_produtos.to_dicts(), start=1):
            registros.append(_agregar_registros(f"id_agrupado_{idx}", [d["chave_produto"]], [d]))
    else:
        chaves_agrupadas: list[str] = []
        for id_agr, chaves in agrupamentos_manuais.items():
            df_grupo = df_produtos.filter(pl.col("chave_produto").is_in(chaves))
            if df_grupo.is_empty():
                continue
            registros.append(_agregar_registros(id_agr, chaves, df_grupo.to_dicts()))
            chaves_agrupadas.extend(chaves)

        df_restante = df_produtos.filter(~pl.col("chave_produto").is_in(chaves_agrupadas))
        idx = len(registros) + 1
        for d in df_restante.to_dicts():
            registros.append(_agregar_registros(f"id_agrupado_{idx}", [d["chave_produto"]], [d]))
            idx += 1

    df_agrupados = pl.DataFrame(registros).select([
        "id_agrupado",
        "lista_chave_produto",
        "descr_padrao",
        "ncm_padrao",
        "cest_padrao",
        "gtin_padrao",
        "lista_co_sefin",
        "co_sefin_padrao",
        "lista_unidades",
        "co_sefin_divergentes",
    ])

    df_final = (
        df_agrupados
        .explode("lista_chave_produto")
        .rename({"lista_chave_produto": "chave_produto"})
        .join(df_produtos, on="chave_produto", how="left")
        .with_columns([
            pl.col("descr_padrao").fill_null(pl.col("descricao")).alias("descr_padrao"),
            pl.col("ncm_padrao").fill_null(pl.col("lista_ncm").map_elements(_moda_simples, return_dtype=pl.String)).alias("ncm_padrao"),
            pl.col("cest_padrao").fill_null(pl.col("lista_cest").map_elements(_moda_simples, return_dtype=pl.String)).alias("cest_padrao"),
            pl.col("gtin_padrao").fill_null(pl.col("lista_gtin").map_elements(_moda_simples, return_dtype=pl.String)).alias("gtin_padrao"),
            pl.col("co_sefin_padrao").fill_null(pl.col("lista_co_sefin").map_elements(_moda_simples, return_dtype=pl.String)).alias("co_sefin_padrao"),
        ])
        .select([
            "id_agrupado",
            "chave_produto",
            "descricao_normalizada",
            "descricao",
            "descr_padrao",
            "ncm_padrao",
            "cest_padrao",
            "gtin_padrao",
            "lista_co_sefin",
            "co_sefin_padrao",
            "co_sefin_divergentes",
            "lista_unidades",
            "lista_desc_compl",
            "lista_codigos",
            "lista_tipo_item",
            "lista_ncm",
            "lista_cest",
            "lista_gtin",
            "lista_unid",
        ])
    )

    salvar_para_parquet(df_agrupados, pasta_produtos, f"produtos_agrupados_{cnpj}.parquet")
    salvar_para_parquet(df_final, pasta_produtos, f"produtos_final_{cnpj}.parquet")

    rprint(f"[green]produtos_agrupados gerado com {len(df_agrupados)} agrupamentos.[/green]")
    rprint(f"[green]produtos_final gerado com {len(df_final)} produtos vinculados.[/green]")
    return df_agrupados


if __name__ == "__main__":
    if len(sys.argv) > 1:
        gerar_produtos_agrupados(sys.argv[1])
    else:
        print("Uso: python produtos_agrupados.py <cnpj>")
