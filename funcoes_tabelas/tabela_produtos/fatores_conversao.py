from __future__ import annotations

import logging
from pathlib import Path

import polars as pl
from rich import print as rprint

from _shared import FUNCOES_DIR, sanitize_cnpj, salvar_para_parquet

logging.basicConfig(level=logging.INFO, format="%(message)s")


def precos_medios_produtos_final(df_unidades: pl.DataFrame) -> pl.DataFrame:
    df_compras = (
        df_unidades.filter(pl.col("compras") > 0)
        .group_by(["id_produtos", "unid"])
        .agg(pl.col("compras").mean().alias("preco_medio_compra"))
    )
    df_vendas = (
        df_unidades.filter(pl.col("vendas") > 0)
        .group_by(["id_produtos", "unid"])
        .agg(pl.col("vendas").mean().alias("preco_medio_venda"))
    )
    return (
        df_unidades.select(["id_produtos", "unid"]).unique()
        .join(df_compras, on=["id_produtos", "unid"], how="left")
        .join(df_vendas, on=["id_produtos", "unid"], how="left")
        .with_columns([
            pl.col("preco_medio_compra").fill_null(0.0),
            pl.col("preco_medio_venda").fill_null(0.0),
        ])
    )


def _carregar_fatores_manuais(pasta_produtos: Path, cnpj: str) -> pl.DataFrame | None:
    candidatos = [
        pasta_produtos / f"fatores_conversao_manuais_{cnpj}.parquet",
        pasta_produtos / f"fatores_conversao_manuais_{cnpj}.xlsx",
    ]
    for caminho in candidatos:
        if not caminho.exists():
            continue
        try:
            df = pl.read_parquet(caminho) if caminho.suffix.lower() == ".parquet" else pl.read_excel(caminho)
        except Exception as exc:
            logging.warning("Aviso: falha ao ler fatores manuais (%s): %s", caminho.name, exc)
            return None
        obrig = {"id_produtos", "unid", "fator"}
        if not obrig.issubset(set(df.columns)):
            logging.warning("Aviso: arquivo manual %s ignorado por schema incompatível.", caminho.name)
            return None
        if "unid_ref" not in df.columns:
            df = df.with_columns(pl.lit(None, dtype=pl.String).alias("unid_ref"))
        return df.select(["id_produtos", "unid", "unid_ref", "fator"]).with_columns([
            pl.col("id_produtos").cast(pl.String),
            pl.col("unid").cast(pl.String),
            pl.col("unid_ref").cast(pl.String),
            pl.col("fator").cast(pl.Float64),
        ])
    return None


def _determinar_unid_ref(group_df: pl.DataFrame) -> str | None:
    contagens = (
        group_df.group_by("unid")
        .agg(pl.len().alias("qtd"))
        .sort(["qtd", "unid"], descending=[True, False])
    )
    if contagens.is_empty():
        return None
    return contagens.get_column("unid")[0]


def gerar_fatores_conversao(cnpj: str, pasta_cnpj: Path | None = None) -> pl.DataFrame | None:
    cnpj = sanitize_cnpj(cnpj)
    if pasta_cnpj is None:
        pasta_cnpj = FUNCOES_DIR / "CNPJ" / cnpj

    pasta_produtos = pasta_cnpj / "analises" / "produtos"
    arq_origens = pasta_produtos / f"produtos_unidades_origens_{cnpj}.parquet"
    arq_mapa_produtos = pasta_produtos / f"produtos_origens_{cnpj}.parquet"
    arq_rastro = pasta_produtos / f"produtos_agrupados_rastro_{cnpj}.parquet"
    arq_final = pasta_produtos / f"produtos_final_{cnpj}.parquet"

    for arquivo in [arq_origens, arq_mapa_produtos, arq_rastro, arq_final]:
        if not arquivo.exists():
            rprint(f"[red]Erro: arquivo necessário não encontrado: {arquivo.name}[/red]")
            return None

    df_origens = pl.read_parquet(arq_origens)
    df_mapa_produtos = pl.read_parquet(arq_mapa_produtos)
    df_rastro = pl.read_parquet(arq_rastro)
    df_final = pl.read_parquet(arq_final)

    df_unidades = (
        df_origens
        .join(df_mapa_produtos.select(["chave_linha_origem", "chave_produto"]), on="chave_linha_origem", how="left")
        .join(df_rastro, on="chave_produto", how="left")
        .rename({"id_agrupado": "id_produtos"})
        .drop_nulls(subset=["id_produtos", "unid"])
    )
    if df_unidades.is_empty():
        rprint("[yellow]Nenhum vínculo rastreável entre origem, produto e agrupamento para cálculo dos fatores.[/yellow]")
        return None

    df_precos = precos_medios_produtos_final(df_unidades)
    fatores = []
    auditoria = []

    for id_prod, group_df in df_precos.group_by("id_produtos"):
        unid_ref = _determinar_unid_ref(group_df)
        if not unid_ref:
            continue
        df_ref = group_df.filter(pl.col("unid") == unid_ref)
        if df_ref.is_empty():
            continue
        preco_ref_compra = float(df_ref.get_column("preco_medio_compra")[0] or 0.0)
        descr_padrao_series = (
            df_final.filter(pl.col("id_agrupado") == id_prod)
            .select("descr_padrao")
            .drop_nulls()
            .to_series()
        )
        descr = descr_padrao_series[0] if len(descr_padrao_series) else None

        for row in group_df.iter_rows(named=True):
            unid = row["unid"]
            preco_compra = float(row["preco_medio_compra"] or 0.0)
            preco_venda = float(row["preco_medio_venda"] or 0.0)
            if unid == unid_ref:
                fator = 1.0
                base_usada = "UNIDADE_REFERENCIA"
            elif preco_compra > 0 and preco_ref_compra > 0:
                fator = preco_compra / preco_ref_compra
                base_usada = "COMPRA/COMPRA_REF"
            elif preco_venda > 0 and preco_ref_compra > 0:
                fator = preco_venda / preco_ref_compra
                base_usada = "VENDA/COMPRA_REF"
            else:
                logging.warning("Aviso: produto %s sem preço médio de compra suficiente para calcular fator da unidade %s.", id_prod, unid)
                auditoria.append({
                    "id_produtos": id_prod,
                    "unid": unid,
                    "unid_ref": unid_ref,
                    "preco_medio_compra": preco_compra,
                    "preco_medio_venda": preco_venda,
                    "preco_ref_compra": preco_ref_compra,
                    "status": "SEM_BASE_SUFICIENTE",
                })
                continue
            fatores.append({
                "id_produtos": id_prod,
                "descr_padrao": descr,
                "unid": unid,
                "unid_ref": unid_ref,
                "fator": fator,
            })
            auditoria.append({
                "id_produtos": id_prod,
                "descr_padrao": descr,
                "unid": unid,
                "unid_ref": unid_ref,
                "preco_medio_compra": preco_compra,
                "preco_medio_venda": preco_venda,
                "preco_ref_compra": preco_ref_compra,
                "base_usada": base_usada,
                "status": "CALCULADO",
            })

    if not fatores:
        rprint("[yellow]Nenhum fator de conversão pôde ser calculado automaticamente.[/yellow]")
        if auditoria:
            salvar_para_parquet(pl.DataFrame(auditoria), pasta_produtos, f"fatores_conversao_auditoria_{cnpj}.parquet")
        return None

    df_fatores = pl.DataFrame(fatores).sort(["id_produtos", "unid"])
    df_manual = _carregar_fatores_manuais(pasta_produtos, cnpj)
    if df_manual is not None:
        df_fatores = df_fatores.join(df_manual, on=["id_produtos", "unid"], how="left", suffix="_manual")
        if "unid_ref_manual" in df_fatores.columns:
            df_fatores = df_fatores.with_columns(pl.coalesce(["unid_ref_manual", "unid_ref"]).alias("unid_ref")).drop("unid_ref_manual")
        if "fator_manual" in df_fatores.columns:
            df_fatores = df_fatores.with_columns(pl.coalesce(["fator_manual", "fator"]).alias("fator")).drop("fator_manual")

    salvar_para_parquet(df_fatores, pasta_produtos, f"fatores_conversao_{cnpj}.parquet")
    salvar_para_parquet(pl.DataFrame(auditoria), pasta_produtos, f"fatores_conversao_auditoria_{cnpj}.parquet")
    salvar_para_parquet(df_precos.sort(["id_produtos", "unid"]), pasta_produtos, f"fatores_conversao_precos_{cnpj}.parquet")
    rprint(f"[green]Fatores de conversão gerados com {len(df_fatores)} registros.[/green]")
    return df_fatores


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        gerar_fatores_conversao(sys.argv[1])
    else:
        print("Uso: python fatores_conversao.py <cnpj>")
