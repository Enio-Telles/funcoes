from __future__ import annotations

import logging
from pathlib import Path

import polars as pl
from rich import print as rprint

from _shared import FUNCOES_DIR, clean_code, clean_punct_code, normalize_text, sanitize_cnpj, salvar_para_parquet

logging.basicConfig(level=logging.INFO, format="%(message)s")

COLUNAS_FINAIS = [
    "codigo",
    "descricao",
    "descr_compl",
    "tipo_item",
    "ncm",
    "cest",
    "co_sefin_item",
    "gtin",
    "unid",
    "compras",
    "vendas",
]

COLUNAS_AUDITORIA = [
    "chave_linha_origem",
    "descricao_normalizada",
    *COLUNAS_FINAIS,
    "fonte",
    "origem_arquivo",
    "tipo_movimento",
]


def _resolver_arquivo(pasta_cnpj: Path, cnpj: str, prefixo: str) -> Path | None:
    try:
        from encontrar_arquivo_cnpj import encontrar_arquivo
    except ImportError:
        def encontrar_arquivo(diretorio, prefixo, cnpj):
            for f in diretorio.glob(f"{prefixo}*{cnpj}*.parquet"):
                return f
            return None

    diretorios = [d for d in (pasta_cnpj / "arquivos_parquet", pasta_cnpj) if d.exists()]
    for diretorio in diretorios:
        arq = encontrar_arquivo(diretorio, prefixo, cnpj)
        if arq:
            return arq
    return None


def _resolver_ref(*partes: str) -> Path | None:
    candidatos = [
        FUNCOES_DIR / "referencias",
        FUNCOES_DIR / "referencias" / "CO_SEFIN",
        FUNCOES_DIR / "referencias" / "co_sefin",
        Path("referencias"),
        Path("referencias") / "CO_SEFIN",
        Path("referencias") / "co_sefin",
    ]
    for base in candidatos:
        caminho = base.joinpath(*partes)
        if caminho.exists():
            return caminho
    return None


def ler_cfop_mercantil() -> pl.DataFrame | None:
    cfop_path = _resolver_ref("cfop", "cfop_bi.parquet") or _resolver_ref("CFOP", "cfop_bi.parquet") or _resolver_ref("cfop_bi.parquet")
    if cfop_path is None:
        logging.warning("Aviso: referência CFOP mercantil não encontrada.")
        return None
    return (
        pl.scan_parquet(cfop_path)
        .filter(pl.col("operacao_mercantil").cast(pl.String) == "X")
        .select(pl.col("co_cfop").cast(pl.String))
        .unique()
        .collect()
    )


def _garantir_colunas(df: pl.DataFrame) -> pl.DataFrame:
    colunas_texto = ["codigo", "descricao", "descr_compl", "tipo_item", "ncm", "cest", "gtin", "unid", "fonte", "origem_arquivo", "tipo_movimento"]
    for col in colunas_texto:
        df = df.with_columns(pl.col(col).cast(pl.String)) if col in df.columns else df.with_columns(pl.lit(None, dtype=pl.String).alias(col))
    for col in ["compras", "vendas"]:
        df = df.with_columns(pl.col(col).fill_null(0).cast(pl.Float64)) if col in df.columns else df.with_columns(pl.lit(0.0).alias(col))
    return df


def _expr_saida(coluna_tipo: str) -> pl.Expr:
    col = pl.col(coluna_tipo).cast(pl.String).str.to_uppercase()
    return col.str.starts_with("1") | col.str.contains("SAID")


def _expr_gtin(df: pl.DataFrame) -> pl.Expr:
    if "prod_ceantrib" in df.columns and "prod_cean" in df.columns:
        return (
            pl.when(pl.col("prod_ceantrib").is_null() | (pl.col("prod_ceantrib").cast(pl.String).str.strip_chars() == ""))
            .then(pl.col("prod_cean"))
            .otherwise(pl.col("prod_ceantrib"))
            .cast(pl.String)
            .alias("gtin")
        )
    if "prod_ceantrib" in df.columns:
        return pl.col("prod_ceantrib").cast(pl.String).alias("gtin")
    if "prod_cean" in df.columns:
        return pl.col("prod_cean").cast(pl.String).alias("gtin")
    return pl.lit(None, dtype=pl.String).alias("gtin")


def processar_nfe_nfce(path: Path | None, cnpj: str, df_cfop: pl.DataFrame | None, fonte: str) -> pl.DataFrame | None:
    if not path or not path.exists():
        return None
    schema = pl.read_parquet(path, n_rows=0).schema
    col_tp = next((c for c in ["tipo_operacao", "co_tp_nf", "tp_nf"] if c in schema), None)
    colunas_base = ["co_emitente", "prod_cprod", "prod_xprod", "prod_ncm", "prod_ucom", "co_cfop", "prod_vprod", "prod_vfrete", "prod_vseg", "prod_voutro", "prod_vdesc"]
    opcionais = ["prod_cest", "prod_ceantrib", "prod_cean"]
    selecionar = [c for c in colunas_base if c in schema] + [c for c in opcionais if c in schema]
    if col_tp:
        selecionar.append(col_tp)
    lf = pl.scan_parquet(path).filter(pl.col("co_emitente").cast(pl.String) == cnpj)
    if col_tp:
        lf = lf.filter(_expr_saida(col_tp))
    if df_cfop is not None and "co_cfop" in schema:
        lf = lf.with_columns(pl.col("co_cfop").cast(pl.String)).join(df_cfop.lazy(), on="co_cfop", how="inner")
    df = lf.select(selecionar).collect()
    if df.is_empty():
        return None
    def _val(col_name: str) -> pl.Expr:
        return pl.col(col_name).fill_null(0).cast(pl.Float64) if col_name in df.columns else pl.lit(0.0)
    df = df.with_columns([
        (_val("prod_vprod") + _val("prod_vfrete") + _val("prod_vseg") + _val("prod_voutro") - _val("prod_vdesc")).alias("vendas"),
        pl.lit(0.0).alias("compras"),
        pl.lit(None, dtype=pl.String).alias("descr_compl"),
        pl.lit(None, dtype=pl.String).alias("tipo_item"),
        _expr_gtin(df),
        pl.lit(fonte).alias("fonte"),
        pl.lit(path.name).alias("origem_arquivo"),
        pl.lit("VENDA").alias("tipo_movimento"),
    ])
    renames = {"prod_cprod": "codigo", "prod_xprod": "descricao", "prod_ncm": "ncm", "prod_ucom": "unid", "prod_cest": "cest"}
    df = df.rename({k: v for k, v in renames.items() if k in df.columns})
    if "cest" not in df.columns:
        df = df.with_columns(pl.lit(None, dtype=pl.String).alias("cest"))
    return _garantir_colunas(df).select(["codigo", "descricao", "descr_compl", "tipo_item", "ncm", "cest", "gtin", "unid", "compras", "vendas", "fonte", "origem_arquivo", "tipo_movimento"])


def processar_c170(path: Path | None, df_cfop: pl.DataFrame | None) -> pl.DataFrame | None:
    if not path or not path.exists():
        return None
    schema = pl.read_parquet(path, n_rows=0).schema
    lf = pl.scan_parquet(path)
    if "ind_oper" in schema:
        lf = lf.filter(pl.col("ind_oper").cast(pl.String) == "0")
    if df_cfop is not None and "co_cfop" in schema:
        lf = lf.with_columns(pl.col("co_cfop").cast(pl.String)).join(df_cfop.lazy(), on="co_cfop", how="inner")
    selecionar = [c for c in ["cod_item", "descr_item", "descr_compl", "tipo_item", "cod_ncm", "cest", "cod_barra", "unid", "valor_item", "vl_item"] if c in schema]
    df = lf.select(selecionar).collect()
    if df.is_empty():
        return None
    df = df.rename({k: v for k, v in {"cod_item": "codigo", "descr_item": "descricao", "cod_ncm": "ncm", "cod_barra": "gtin"}.items() if k in df.columns})
    valor_col = "vl_item" if "vl_item" in df.columns else "valor_item"
    df = df.with_columns([
        (pl.col(valor_col).fill_null(0).cast(pl.Float64) if valor_col in df.columns else pl.lit(0.0)).alias("compras"),
        pl.lit(0.0).alias("vendas"),
        pl.lit("C170").alias("fonte"),
        pl.lit(path.name).alias("origem_arquivo"),
        pl.lit("COMPRA").alias("tipo_movimento"),
    ])
    return _garantir_colunas(df).select(["codigo", "descricao", "descr_compl", "tipo_item", "ncm", "cest", "gtin", "unid", "compras", "vendas", "fonte", "origem_arquivo", "tipo_movimento"])


def processar_bloco_h(path: Path | None) -> pl.DataFrame | None:
    if not path or not path.exists():
        return None
    schema = pl.read_parquet(path, n_rows=0).schema
    selecionar = [c for c in ["codigo_produto", "codigo_produto_original", "descricao_produto", "tipo_item", "cod_ncm", "cest", "cod_barra", "unidade_medida"] if c in schema]
    df = pl.scan_parquet(path).select(selecionar).collect()
    if df.is_empty():
        return None
    if "codigo_produto" in df.columns:
        df = df.rename({"codigo_produto": "codigo"})
    elif "codigo_produto_original" in df.columns:
        df = df.rename({"codigo_produto_original": "codigo"})
    df = df.rename({k: v for k, v in {"descricao_produto": "descricao", "cod_ncm": "ncm", "cod_barra": "gtin", "unidade_medida": "unid"}.items() if k in df.columns})
    df = df.with_columns([
        pl.lit(None, dtype=pl.String).alias("descr_compl"),
        pl.lit(0.0).alias("compras"),
        pl.lit(0.0).alias("vendas"),
        pl.lit("BLOCO_H").alias("fonte"),
        pl.lit(path.name).alias("origem_arquivo"),
        pl.lit("ESTOQUE").alias("tipo_movimento"),
    ])
    return _garantir_colunas(df).select(["codigo", "descricao", "descr_compl", "tipo_item", "ncm", "cest", "gtin", "unid", "compras", "vendas", "fonte", "origem_arquivo", "tipo_movimento"])


def _detectar_coluna(df: pl.DataFrame, alternativas: list[str]) -> str | None:
    for col in alternativas:
        if col in df.columns:
            return col
    return None


def _load_ref(path: Path | None, alternativas: dict[str, list[str]]) -> pl.DataFrame | None:
    if path is None or not path.exists():
        return None
    df = pl.read_parquet(path)
    renames = {}
    for destino, candidatas in alternativas.items():
        col = _detectar_coluna(df, candidatas)
        if col:
            renames[col] = destino
    if "co_sefin" not in renames.values():
        return None
    df = df.select(list(renames.keys())).rename(renames)
    for col in ["ncm", "cest", "co_sefin"]:
        if col in df.columns:
            df = df.with_columns(pl.col(col).cast(pl.String))
    return df.unique()


def _carregar_refs_co_sefin() -> tuple[pl.DataFrame | None, pl.DataFrame | None, pl.DataFrame | None]:
    return (
        _load_ref(_resolver_ref("sitafe_cest_ncm.parquet"), {"ncm": ["it_nu_ncm", "ncm"], "cest": ["it_nu_cest", "cest"], "co_sefin": ["it_co_sefin", "co_sefin"]}),
        _load_ref(_resolver_ref("sitafe_cest.parquet"), {"cest": ["it_nu_cest", "cest"], "co_sefin": ["it_co_sefin", "co_sefin"]}),
        _load_ref(_resolver_ref("sitafe_ncm.parquet"), {"ncm": ["it_nu_ncm", "ncm"], "co_sefin": ["it_co_sefin", "co_sefin"]}),
    )


def adicionar_co_sefin(df: pl.DataFrame) -> pl.DataFrame:
    if df.is_empty():
        return df.with_columns(pl.lit(None, dtype=pl.String).alias("co_sefin_item"))
    df = df.with_columns([
        pl.col("ncm").map_elements(clean_punct_code, return_dtype=pl.String).alias("_ncm_ref"),
        pl.col("cest").map_elements(clean_punct_code, return_dtype=pl.String).alias("_cest_ref"),
    ])
    ref_cest_ncm, ref_cest, ref_ncm = _carregar_refs_co_sefin()
    if ref_cest_ncm is not None:
        ref_cest_ncm = ref_cest_ncm.with_columns([
            pl.col("ncm").map_elements(clean_punct_code, return_dtype=pl.String).alias("_ncm_ref"),
            pl.col("cest").map_elements(clean_punct_code, return_dtype=pl.String).alias("_cest_ref"),
            pl.col("co_sefin").cast(pl.String).alias("_co_sefin_cest_ncm"),
        ]).select(["_ncm_ref", "_cest_ref", "_co_sefin_cest_ncm"])
        df = df.join(ref_cest_ncm, on=["_ncm_ref", "_cest_ref"], how="left")
    if ref_cest is not None:
        ref_cest = ref_cest.with_columns([
            pl.col("cest").map_elements(clean_punct_code, return_dtype=pl.String).alias("_cest_ref"),
            pl.col("co_sefin").cast(pl.String).alias("_co_sefin_cest"),
        ]).select(["_cest_ref", "_co_sefin_cest"])
        df = df.join(ref_cest, on="_cest_ref", how="left")
    if ref_ncm is not None:
        ref_ncm = ref_ncm.with_columns([
            pl.col("ncm").map_elements(clean_punct_code, return_dtype=pl.String).alias("_ncm_ref"),
            pl.col("co_sefin").cast(pl.String).alias("_co_sefin_ncm"),
        ]).select(["_ncm_ref", "_co_sefin_ncm"])
        df = df.join(ref_ncm, on="_ncm_ref", how="left")
    return df.with_columns(pl.coalesce(["_co_sefin_cest_ncm", "_co_sefin_cest", "_co_sefin_ncm"]).alias("co_sefin_item")).drop([c for c in ["_ncm_ref", "_cest_ref", "_co_sefin_cest_ncm", "_co_sefin_cest", "_co_sefin_ncm"] if c in df.columns])


def gerar_produtos_unidades(cnpj: str, pasta_cnpj: Path | None = None) -> pl.DataFrame | None:
    cnpj = sanitize_cnpj(cnpj)
    if pasta_cnpj is None:
        pasta_cnpj = FUNCOES_DIR / "CNPJ" / cnpj
    df_cfop = ler_cfop_mercantil()
    candidatos = [
        processar_nfe_nfce(_resolver_arquivo(pasta_cnpj, cnpj, "NFe"), cnpj, df_cfop, "NFe"),
        processar_nfe_nfce(_resolver_arquivo(pasta_cnpj, cnpj, "NFCe"), cnpj, df_cfop, "NFCe"),
        processar_c170(_resolver_arquivo(pasta_cnpj, cnpj, "c170_simplificada") or _resolver_arquivo(pasta_cnpj, cnpj, "c170"), df_cfop),
        processar_bloco_h(_resolver_arquivo(pasta_cnpj, cnpj, "bloco_h")),
    ]
    fragmentos = [df for df in candidatos if df is not None and not df.is_empty()]
    if not fragmentos:
        rprint("[red]Nenhuma fonte encontrada para gerar produtos_unidades.[/red]")
        return None
    df_total = pl.concat(fragmentos, how="diagonal_relaxed")
    df_total = _garantir_colunas(df_total).with_columns([
        pl.col("codigo").map_elements(clean_code, return_dtype=pl.String).alias("codigo"),
        pl.col("descricao").map_elements(normalize_text, return_dtype=pl.String).alias("descricao"),
        pl.col("descr_compl").map_elements(normalize_text, return_dtype=pl.String).alias("descr_compl"),
        pl.col("tipo_item").map_elements(normalize_text, return_dtype=pl.String).alias("tipo_item"),
        pl.col("ncm").map_elements(clean_punct_code, return_dtype=pl.String).alias("ncm"),
        pl.col("cest").map_elements(clean_punct_code, return_dtype=pl.String).alias("cest"),
        pl.col("gtin").map_elements(clean_punct_code, return_dtype=pl.String).alias("gtin"),
        pl.col("unid").map_elements(normalize_text, return_dtype=pl.String).alias("unid"),
        pl.col("descricao").map_elements(normalize_text, return_dtype=pl.String).alias("descricao_normalizada"),
    ])
    df_total = adicionar_co_sefin(df_total).with_columns((pl.lit("origem_") + pl.int_range(1, pl.len() + 1).cast(pl.String)).alias("chave_linha_origem"))
    for col in COLUNAS_AUDITORIA:
        if col not in df_total.columns:
            df_total = df_total.with_columns(pl.lit(0.0).alias(col) if col in {"compras", "vendas"} else pl.lit(None, dtype=pl.String).alias(col))
    pasta_saida = pasta_cnpj / "analises" / "produtos"
    salvar_para_parquet(df_total.select(COLUNAS_AUDITORIA), pasta_saida, f"produtos_unidades_origens_{cnpj}.parquet")
    df_saida = df_total.select(COLUNAS_FINAIS)
    salvar_para_parquet(df_saida, pasta_saida, f"produtos_unidades_{cnpj}.parquet")
    rprint(f"[green]produtos_unidades gerado com {len(df_saida)} registros.[/green]")
    return df_saida
