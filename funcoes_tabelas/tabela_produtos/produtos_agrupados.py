"""
Módulo: produtos_agrupados.py
Objetivo: permitir a união manual de linhas da tabela produtos em uma nova
Tabela produtos_agrupados e recalcular produtos_final com rastreabilidade.
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

FONTES_EMITIDAS = {"NFe", "NFCe"}


def _sanitizar_cnpj(cnpj: str) -> str:
    return re.sub(r"[^0-9]", "", str(cnpj))


def _limpos(lista: list[str] | None) -> list[str]:
    if not lista:
        return []
    return [str(x).strip() for x in lista if x not in (None, "", []) and str(x).strip()]


def _moda(lista: list[str] | None) -> str | None:
    vals = _limpos(lista)
    if not vals:
        return None
    cont = Counter(vals)
    maior = max(cont.values())
    candidatos = [k for k, v in cont.items() if v == maior]
    candidatos.sort(key=lambda x: (len(x), x), reverse=True)
    return candidatos[0]


def _divergente(lista: list[str] | None) -> bool:
    return len(set(_limpos(lista))) > 1


def _campos_preenchidos(reg: dict) -> int:
    return sum(1 for campo in ["ncm", "cest", "gtin"] if reg.get(campo) not in (None, ""))


def _escolher_valor_padrao(df_src: pl.DataFrame, coluna: str, preferir_emitidas: bool = True) -> str | None:
    if coluna not in df_src.columns:
        return None

    base = df_src.filter(pl.col(coluna).is_not_null() & (pl.col(coluna).cast(pl.String).str.strip_chars() != ""))
    if base.is_empty():
        return None

    if preferir_emitidas and "fonte" in base.columns:
        emitidas = base.filter(pl.col("fonte").is_in(list(FONTES_EMITIDAS)))
        if not emitidas.is_empty():
            base = emitidas

    agrup = base.group_by(coluna).agg([
        pl.len().alias("freq"),
        pl.sum_horizontal([
            pl.when(pl.col("ncm").is_not_null() & (pl.col("ncm").cast(pl.String).str.strip_chars() != "")).then(1).otherwise(0),
            pl.when(pl.col("cest").is_not_null() & (pl.col("cest").cast(pl.String).str.strip_chars() != "")).then(1).otherwise(0),
            pl.when(pl.col("gtin").is_not_null() & (pl.col("gtin").cast(pl.String).str.strip_chars() != "")).then(1).otherwise(0),
        ]).max().alias("preenchidos"),
        pl.when(pl.col("descricao").is_not_null()).then(pl.col("descricao").cast(pl.String).str.len_chars()).otherwise(0).max().alias("tam_desc"),
    ]).sort(["freq", "preenchidos", "tam_desc", coluna], descending=[True, True, True, False])

    return agrup.get_column(coluna)[0] if agrup.height else None


def _agregar_registros(id_agrupado: str, chaves: list[str], df_produtos: pl.DataFrame, df_origens: pl.DataFrame | None) -> dict:
    df_grp = df_produtos.filter(pl.col("chave_produto").is_in(chaves))
    origens = None
    if df_origens is not None and not df_origens.is_empty():
        origens = df_origens.filter(pl.col("chave_produto").is_in(chaves))

    lista_co_sefin = sorted(set(item for row in df_grp.get_column("lista_co_sefin").to_list() for item in _limpos(row))) if "lista_co_sefin" in df_grp.columns else []
    lista_unidades = sorted(set(item for row in df_grp.get_column("lista_unid").to_list() for item in _limpos(row))) if "lista_unid" in df_grp.columns else []

    descr_padrao = None
    ncm_padrao = None
    cest_padrao = None
    gtin_padrao = None
    co_sefin_padrao = None

    if origens is not None and not origens.is_empty():
        descr_padrao = _escolher_valor_padrao(origens, "descricao", preferir_emitidas=True)
        ncm_padrao = _escolher_valor_padrao(origens, "ncm", preferir_emitidas=True)
        cest_padrao = _escolher_valor_padrao(origens, "cest", preferir_emitidas=True)
        gtin_padrao = _escolher_valor_padrao(origens, "gtin", preferir_emitidas=True)
        co_sefin_padrao = _escolher_valor_padrao(origens, "co_sefin_item", preferir_emitidas=True)

    if descr_padrao is None:
        descr_padrao = _moda(df_grp.get_column("descricao").to_list()) if "descricao" in df_grp.columns else None
    if ncm_padrao is None:
        ncm_padrao = _moda([item for row in df_grp.get_column("lista_ncm").to_list() for item in _limpos(row)]) if "lista_ncm" in df_grp.columns else None
    if cest_padrao is None:
        cest_padrao = _moda([item for row in df_grp.get_column("lista_cest").to_list() for item in _limpos(row)]) if "lista_cest" in df_grp.columns else None
    if gtin_padrao is None:
        gtin_padrao = _moda([item for row in df_grp.get_column("lista_gtin").to_list() for item in _limpos(row)]) if "lista_gtin" in df_grp.columns else None
    if co_sefin_padrao is None:
        co_sefin_padrao = _moda(lista_co_sefin)

    return {
        "id_agrupado": id_agrupado,
        "lista_chave_produto": sorted(set(chaves)),
        "descr_padrao": descr_padrao,
        "ncm_padrao": ncm_padrao,
        "cest_padrao": cest_padrao,
        "gtin_padrao": gtin_padrao,
        "lista_co_sefin": lista_co_sefin,
        "co_sefin_padrao": co_sefin_padrao,
        "lista_unidades": lista_unidades,
        "co_sefin_divergentes": _divergente(lista_co_sefin),
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
    arq_origens = pasta_produtos / f"produtos_unidades_origens_{cnpj}.parquet"
    arq_mapa = pasta_produtos / f"produtos_origens_{cnpj}.parquet"

    if not arq_produtos.exists():
        rprint(f"[red]Erro: Tabela base {arq_produtos} não encontrada.[/red]")
        return None

    df_produtos = pl.read_parquet(arq_produtos)
    if df_produtos.is_empty():
        return None

    df_origens = None
    if arq_origens.exists() and arq_mapa.exists():
        df_origens = (
            pl.read_parquet(arq_origens)
            .join(pl.read_parquet(arq_mapa).select(["chave_linha_origem", "chave_produto"]), on="chave_linha_origem", how="left")
        )

    registros: list[dict] = []
    rastros: list[dict] = []

    if not agrupamentos_manuais:
        for idx, d in enumerate(df_produtos.to_dicts(), start=1):
            chaves = [d["chave_produto"]]
            id_agrupado = f"id_agrupado_{idx}"
            registros.append(_agregar_registros(id_agrupado, chaves, df_produtos, df_origens))
            rastros.extend({"id_agrupado": id_agrupado, "chave_produto": ch} for ch in chaves)
    else:
        chaves_agrupadas: list[str] = []
        for id_agr, chaves in agrupamentos_manuais.items():
            df_grupo = df_produtos.filter(pl.col("chave_produto").is_in(chaves))
            if df_grupo.is_empty():
                continue
            registros.append(_agregar_registros(id_agr, chaves, df_produtos, df_origens))
            rastros.extend({"id_agrupado": id_agr, "chave_produto": ch} for ch in chaves)
            chaves_agrupadas.extend(chaves)

        df_restante = df_produtos.filter(~pl.col("chave_produto").is_in(chaves_agrupadas))
        idx = len(registros) + 1
        for d in df_restante.to_dicts():
            id_agrupado = f"id_agrupado_{idx}"
            chaves = [d["chave_produto"]]
            registros.append(_agregar_registros(id_agrupado, chaves, df_produtos, df_origens))
            rastros.extend({"id_agrupado": id_agrupado, "chave_produto": ch} for ch in chaves)
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

    df_rastro = pl.DataFrame(rastros)

    df_final = (
        df_rastro
        .join(df_produtos, on="chave_produto", how="left")
        .join(df_agrupados.drop("lista_chave_produto"), on="id_agrupado", how="left")
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
    salvar_para_parquet(df_rastro, pasta_produtos, f"produtos_agrupados_rastro_{cnpj}.parquet")

    if df_origens is not None and not df_origens.is_empty():
        auditoria = df_origens.join(df_rastro, on="chave_produto", how="left")
        salvar_para_parquet(auditoria, pasta_produtos, f"produtos_final_origens_{cnpj}.parquet")

    rprint(f"[green]produtos_agrupados gerado com {len(df_agrupados)} agrupamentos.[/green]")
    rprint(f"[green]produtos_final gerado com {len(df_final)} produtos vinculados.[/green]")
    return df_agrupados


if __name__ == "__main__":
    if len(sys.argv) > 1:
        gerar_produtos_agrupados(sys.argv[1])
    else:
        print("Uso: python produtos_agrupados.py <cnpj>")
