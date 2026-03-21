from __future__ import annotations

from pathlib import Path

import polars as pl
from rich import print as rprint

from _shared import FUNCOES_DIR, normalize_text, sanitize_cnpj, salvar_para_parquet


def _escolher_descricao_principal(df_grp: pl.DataFrame) -> str | None:
    if df_grp.is_empty():
        return None
    colunas = set(df_grp.columns)
    tem_fonte = "fonte" in colunas
    preferencias = ["NFe", "NFCe"]
    if tem_fonte:
        df_emitidas = df_grp.filter(pl.col("fonte").is_in(preferencias) & pl.col("descricao").is_not_null())
        base = df_emitidas if not df_emitidas.is_empty() else df_grp.filter(pl.col("descricao").is_not_null())
    else:
        base = df_grp.filter(pl.col("descricao").is_not_null())
    if base.is_empty():
        return None
    ranking = (
        base.group_by("descricao")
        .agg([pl.len().alias("freq"), pl.col("descricao").str.len_chars().max().alias("tam")])
        .sort(["freq", "tam", "descricao"], descending=[True, True, False])
    )
    return ranking.get_column("descricao")[0] if ranking.height else None


def gerar_tabela_produtos(cnpj: str, pasta_cnpj: Path | None = None) -> pl.DataFrame | None:
    cnpj = sanitize_cnpj(cnpj)
    if pasta_cnpj is None:
        pasta_cnpj = FUNCOES_DIR / "CNPJ" / cnpj
    pasta_produtos = pasta_cnpj / "analises" / "produtos"
    arq_unidades = pasta_produtos / f"produtos_unidades_{cnpj}.parquet"
    arq_origens = pasta_produtos / f"produtos_unidades_origens_{cnpj}.parquet"
    if not arq_unidades.exists():
        rprint(f"[red]Erro: Tabela base {arq_unidades} não encontrada.[/red]")
        return None
    df = pl.read_parquet(arq_unidades)
    if df.is_empty():
        return None
    if "co_sefin_item" not in df.columns:
        df = df.with_columns(pl.lit(None, dtype=pl.String).alias("co_sefin_item"))
    df = df.with_columns(pl.col("descricao").map_elements(normalize_text, return_dtype=pl.String).alias("descricao_normalizada"))

    grupos = []
    for idx, (desc_norm, grp) in enumerate(df.group_by("descricao_normalizada"), start=1):
        grupos.append({
            "chave_produto": f"id_produto_{idx}",
            "descricao_normalizada": desc_norm,
            "descricao": _escolher_descricao_principal(grp),
            "lista_desc_compl": sorted(set(x for x in grp.get_column("descr_compl").to_list() if x not in (None, ""))),
            "lista_codigos": sorted(set(x for x in grp.get_column("codigo").to_list() if x not in (None, ""))),
            "lista_tipo_item": sorted(set(x for x in grp.get_column("tipo_item").to_list() if x not in (None, ""))),
            "lista_ncm": sorted(set(x for x in grp.get_column("ncm").to_list() if x not in (None, ""))),
            "lista_cest": sorted(set(x for x in grp.get_column("cest").to_list() if x not in (None, ""))),
            "lista_gtin": sorted(set(x for x in grp.get_column("gtin").to_list() if x not in (None, ""))),
            "lista_co_sefin": sorted(set(x for x in grp.get_column("co_sefin_item").to_list() if x not in (None, ""))),
            "lista_unid": sorted(set(x for x in grp.get_column("unid").to_list() if x not in (None, ""))),
        })
    df_agrupado = pl.DataFrame(grupos).sort("descricao_normalizada")
    salvar_para_parquet(df_agrupado, pasta_produtos, f"produtos_{cnpj}.parquet")

    if arq_origens.exists():
        df_origens = pl.read_parquet(arq_origens)
        mapa = (
            df_origens.select(["chave_linha_origem", "descricao_normalizada", "fonte", "origem_arquivo", "tipo_movimento"])
            .join(df_agrupado.select(["descricao_normalizada", "chave_produto"]), on="descricao_normalizada", how="left")
            .select(["chave_linha_origem", "descricao_normalizada", "chave_produto", "fonte", "origem_arquivo", "tipo_movimento"])
        )
        salvar_para_parquet(mapa, pasta_produtos, f"produtos_origens_{cnpj}.parquet")

    rprint(f"[green]produtos gerado com {len(df_agrupado)} registros.[/green]")
    return df_agrupado
