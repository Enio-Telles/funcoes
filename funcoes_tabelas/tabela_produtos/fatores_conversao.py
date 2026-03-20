"""
Módulo: fatores_conversao.py
Objetivo: calcular a relação entre diferentes unidades de medida do mesmo produto.
"""

from __future__ import annotations

import logging
import re
import sys
import unicodedata
from pathlib import Path

import polars as pl
from rich import print as rprint

logging.basicConfig(level=logging.INFO, format="%(message)s")

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


def _normalizar_texto(v: str | None) -> str | None:
    if v is None:
        return None
    v = unicodedata.normalize("NFD", str(v))
    v = "".join(c for c in v if unicodedata.category(c) != "Mn")
    return " ".join(v.upper().strip().split()) or None


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
    cnpj = _sanitizar_cnpj(cnpj)
    if pasta_cnpj is None:
        pasta_cnpj = FUNCOES_DIR / "CNPJ" / cnpj

    pasta_produtos = pasta_cnpj / "analises" / "produtos"
    arq_unidades = pasta_produtos / f"produtos_unidades_{cnpj}.parquet"
    arq_final = pasta_produtos / f"produtos_final_{cnpj}.parquet"

    if not arq_unidades.exists():
        rprint(f"[red]Erro: Tabela de unidades não encontrada em {arq_unidades}.[/red]")
        return None
    if not arq_final.exists():
        rprint(f"[red]Erro: Tabela produtos_final não encontrada em {arq_final}.[/red]")
        return None

    df_unidades = pl.read_parquet(arq_unidades).with_columns(
        pl.col("descricao").map_elements(_normalizar_texto, return_dtype=pl.String).alias("descricao_normalizada")
    )
    df_final = pl.read_parquet(arq_final)

    if "id_agrupado" not in df_final.columns:
        rprint("[red]Erro: produtos_final sem coluna id_agrupado.[/red]")
        return None

    mapa = df_final.select(["descricao_normalizada", "id_agrupado", "descr_padrao", "lista_unidades"]).unique()
    df_unidades = (
        df_unidades
        .join(mapa, on="descricao_normalizada", how="left")
        .rename({"id_agrupado": "id_produtos"})
        .drop_nulls(subset=["id_produtos", "unid"])
    )

    if df_unidades.is_empty():
        rprint("[yellow]Nenhum vínculo entre produtos_unidades e produtos_final para cálculo dos fatores.[/yellow]")
        return None

    df_precos = precos_medios_produtos_final(df_unidades)
    fatores = []

    for id_prod, group_df in df_precos.group_by("id_produtos"):
        unid_ref = _determinar_unid_ref(group_df)
        if not unid_ref:
            continue

        df_ref = group_df.filter(pl.col("unid") == unid_ref)
        if df_ref.is_empty():
            continue

        preco_ref_compra = float(df_ref.get_column("preco_medio_compra")[0] or 0.0)
        descr_padrao_series = (
            df_unidades.filter(pl.col("id_produtos") == id_prod)
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
            elif preco_compra > 0 and preco_ref_compra > 0:
                fator = preco_compra / preco_ref_compra
            elif preco_venda > 0 and preco_ref_compra > 0:
                fator = preco_venda / preco_ref_compra
            else:
                logging.warning(
                    "Aviso: produto %s sem preço médio de compra suficiente para calcular fator da unidade %s.",
                    id_prod,
                    unid,
                )
                continue

            fatores.append(
                {
                    "id_produtos": id_prod,
                    "descr_padrao": descr,
                    "unid": unid,
                    "unid_ref": unid_ref,
                    "fator": fator,
                }
            )

    if not fatores:
        rprint("[yellow]Nenhum fator de conversão pôde ser calculado automaticamente.[/yellow]")
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
    rprint(f"[green]Fatores de conversão gerados com {len(df_fatores)} registros.[/green]")
    return df_fatores


if __name__ == "__main__":
    if len(sys.argv) > 1:
        gerar_fatores_conversao(sys.argv[1])
    else:
        print("Uso: python fatores_conversao.py <cnpj>")
