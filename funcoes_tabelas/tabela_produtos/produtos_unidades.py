"""
Módulo: produtos_unidades.py
Objetivo: gerar a tabela base de movimentações por unidade.
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
    from encontrar_arquivo_cnpj import encontrar_arquivo
except ImportError:
    def salvar_para_parquet(df, pasta, nome):
        pasta.mkdir(parents=True, exist_ok=True)
        df.write_parquet(pasta / nome)
        return True

    def encontrar_arquivo(diretorio, prefixo, cnpj):
        for f in diretorio.glob(f"{prefixo}*{cnpj}*.parquet"):
            return f
        return None


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


def _sanitizar_cnpj(cnpj: str) -> str:
    return re.sub(r"[^0-9]", "", str(cnpj))


def _normalizar_texto(v: str | None) -> str | None:
    if v is None:
        return None
    v = unicodedata.normalize("NFD", str(v))
    v = "".join(c for c in v if unicodedata.category(c) != "Mn")
    return " ".join(v.upper().strip().split()) or None


def _limpar_codigo(v: str | None) -> str | None:
    txt = _normalizar_texto(v)
    if txt is None:
        return None
    return txt.lstrip("0") or "0"


def _limpar_codigo_pontuado(v: str | None) -> str | None:
    txt = _normalizar_texto(v)
    if txt is None:
        return None
    return re.sub(r"[^0-9A-Z]", "", txt) or None


def _resolver_arquivo(pasta_cnpj: Path, cnpj: str, prefixo: str) -> Path | None:
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
    cfop_path = (
        _resolver_ref("cfop", "cfop_bi.parquet")
        or _resolver_ref("CFOP", "cfop_bi.parquet")
        or _resolver_ref("cfop_bi.parquet")
    )
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


def _aplicar_schema_padrao(df: pl.DataFrame) -> pl.DataFrame:
    for col in ["codigo", "descricao", "descr_compl", "tipo_item", "ncm", "cest", "gtin", "unid"]:
        if col in df.columns:
            df = df.with_columns(pl.col(col).cast(pl.String))
        else:
            df = df.with_columns(pl.lit(None, dtype=pl.String).alias(col))

    for col in ["compras", "vendas"]:
        if col in df.columns:
            df = df.with_columns(pl.col(col).fill_null(0).cast(pl.Float64))
        else:
            df = df.with_columns(pl.lit(0.0).alias(col))
    return df


def _expr_saida(coluna_tipo: str) -> pl.Expr:
    col = pl.col(coluna_tipo).cast(pl.String).str.to_uppercase()
    return col.str.starts_with("1") | col.str.contains("SAID")


def processar_nfe_nfce(path: Path | None, cnpj: str, df_cfop: pl.DataFrame | None) -> pl.DataFrame | None:
    if not path or not path.exists():
        return None

    schema = pl.read_parquet(path, n_rows=0).schema
    col_tp = next((c for c in ["tipo_operacao", "co_tp_nf", "tp_nf"] if c in schema), None)

    colunas_base = [
        "co_emitente",
        "prod_cprod",
        "prod_xprod",
        "prod_ncm",
        "prod_ucom",
        "co_cfop",
        "prod_vprod",
        "prod_vfrete",
        "prod_vseg",
        "prod_voutro",
        "prod_vdesc",
    ]
    opcionais = ["prod_cest", "prod_ceantrib", "prod_cean"]
    selecionar = [c for c in colunas_base if c in schema] + [c for c in opcionais if c in schema]
    if col_tp:
        selecionar.append(col_tp)

    lf = pl.scan_parquet(path).filter(pl.col("co_emitente").cast(pl.String) == cnpj)
    if col_tp:
        lf = lf.filter(_expr_saida(col_tp))

    if df_cfop is not None and "co_cfop" in schema:
        lf = lf.with_columns(pl.col("co_cfop").cast(pl.String))
        lf = lf.join(df_cfop.lazy(), on="co_cfop", how="inner")

    df = lf.select(selecionar).collect()
    if df.is_empty():
        return None

    def _val(col_name: str) -> pl.Expr:
        if col_name in df.columns:
            return pl.col(col_name).fill_null(0).cast(pl.Float64)
        return pl.lit(0.0)

    if "prod_ceantrib" in df.columns and "prod_cean" in df.columns:
        gtin_expr = (
            pl.when(pl.col("prod_ceantrib").is_null() | (pl.col("prod_ceantrib").cast(pl.String).str.strip_chars() == ""))
            .then(pl.col("prod_cean"))
            .otherwise(pl.col("prod_ceantrib"))
            .cast(pl.String)
            .alias("gtin")
        )
    elif "prod_ceantrib" in df.columns:
        gtin_expr = pl.col("prod_ceantrib").cast(pl.String).alias("gtin")
    elif "prod_cean" in df.columns:
        gtin_expr = pl.col("prod_cean").cast(pl.String).alias("gtin")
    else:
        gtin_expr = pl.lit(None, dtype=pl.String).alias("gtin")

    df = df.with_columns([
        (_val("prod_vprod") + _val("prod_vfrete") + _val("prod_vseg") + _val("prod_voutro") - _val("prod_vdesc")).alias("vendas"),
        pl.lit(0.0).alias("compras"),
        pl.lit(None, dtype=pl.String).alias("descr_compl"),
        pl.lit(None, dtype=pl.String).alias("tipo_item"),
        gtin_expr,
    ])

    renames = {
        "prod_cprod": "codigo",
        "prod_xprod": "descricao",
        "prod_ncm": "ncm",
        "prod_ucom": "unid",
        "prod_cest": "cest",
    }
    df = df.rename({k: v for k, v in renames.items() if k in df.columns})
    if "cest" not in df.columns:
        df = df.with_columns(pl.lit(None, dtype=pl.String).alias("cest"))

    return _aplicar_schema_padrao(df).select(
        ["codigo", "descricao", "descr_compl", "tipo_item", "ncm", "cest", "gtin", "unid", "compras", "vendas"]
    )


def processar_c170(path: Path | None, df_cfop: pl.DataFrame | None) -> pl.DataFrame | None:
    if not path or not path.exists():
        return None

    schema = pl.read_parquet(path, n_rows=0).schema
    lf = pl.scan_parquet(path)

    if "ind_oper" in schema:
        lf = lf.filter(pl.col("ind_oper").cast(pl.String) == "0")
    if df_cfop is not None and "co_cfop" in schema:
        lf = lf.with_columns(pl.col("co_cfop").cast(pl.String))
        lf = lf.join(df_cfop.lazy(), on="co_cfop", how="inner")

    selecionar = [c for c in ["cod_item", "descr_item", "descr_compl", "tipo_item", "cod_ncm", "cest", "cod_barra", "unid", "valor_item", "vl_item"] if c in schema]
    df = lf.select(selecionar).collect()
    if df.is_empty():
        return None

    renames = {
        "cod_item": "codigo",
        "descr_item": "descricao",
        "cod_ncm": "ncm",
        "cod_barra": "gtin",
    }
    df = df.rename({k: v for k, v in renames.items() if k in df.columns})

    valor_col = "vl_item" if "vl_item" in df.columns else "valor_item"
    if valor_col in df.columns:
        df = df.with_columns(pl.col(valor_col).fill_null(0).cast(pl.Float64).alias("compras"))
    else:
        df = df.with_columns(pl.lit(0.0).alias("compras"))

    df = df.with_columns(pl.lit(0.0).alias("vendas"))
    return _aplicar_schema_padrao(df).select(
        ["codigo", "descricao", "descr_compl", "tipo_item", "ncm", "cest", "gtin", "unid", "compras", "vendas"]
    )


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

    renames = {
        "descricao_produto": "descricao",
        "cod_ncm": "ncm",
        "cod_barra": "gtin",
        "unidade_medida": "unid",
    }
    df = df.rename({k: v for k, v in renames.items() if k in df.columns})
    df = df.with_columns([
        pl.lit(None, dtype=pl.String).alias("descr_compl"),
        pl.lit(0.0).alias("compras"),
        pl.lit(0.0).alias("vendas"),
    ])
    return _aplicar_schema_padrao(df).select(
        ["codigo", "descricao", "descr_compl", "tipo_item", "ncm", "cest", "gtin", "unid", "compras", "vendas"]
    )


def _detectar_colunas(df: pl.DataFrame, alternativas: list[str]) -> str | None:
    for col in alternativas:
        if col in df.columns:
            return col
    return None


def _load_ref(path: Path | None, alternativas: dict[str, list[str]]) -> pl.DataFrame | None:
    if path is None or not path.exists():
        return None
    df = pl.read_parquet(path)
    renames: dict[str, str] = {}
    for destino, candidatas in alternativas.items():
        col = _detectar_colunas(df, candidatas)
        if col:
            renames[col] = destino

    if "co_sefin" not in renames.values():
        return None

    cols = list(renames.keys())
    df = df.select(cols).rename(renames)
    for col in ["ncm", "cest", "co_sefin"]:
        if col in df.columns:
            df = df.with_columns(pl.col(col).cast(pl.String))
    return df.unique()


def _carregar_refs_co_sefin() -> tuple[pl.DataFrame | None, pl.DataFrame | None, pl.DataFrame | None]:
    ref_cest_ncm = _load_ref(
        _resolver_ref("sitafe_cest_ncm.parquet"),
        {
            "ncm": ["it_nu_ncm", "ncm"],
            "cest": ["it_nu_cest", "cest"],
            "co_sefin": ["it_co_sefin", "co_sefin"],
        },
    )
    ref_cest = _load_ref(
        _resolver_ref("sitafe_cest.parquet"),
        {
            "cest": ["it_nu_cest", "cest"],
            "co_sefin": ["it_co_sefin", "co_sefin"],
        },
    )
    ref_ncm = _load_ref(
        _resolver_ref("sitafe_ncm.parquet"),
        {
            "ncm": ["it_nu_ncm", "ncm"],
            "co_sefin": ["it_co_sefin", "co_sefin"],
        },
    )
    return ref_cest_ncm, ref_cest, ref_ncm


def adicionar_co_sefin(df: pl.DataFrame) -> pl.DataFrame:
    if df.is_empty():
        return df.with_columns(pl.lit(None, dtype=pl.String).alias("co_sefin_item"))

    df = df.with_columns([
        pl.col("ncm").map_elements(_limpar_codigo_pontuado, return_dtype=pl.String).alias("_ncm_ref"),
        pl.col("cest").map_elements(_limpar_codigo_pontuado, return_dtype=pl.String).alias("_cest_ref"),
    ])

    ref_cest_ncm, ref_cest, ref_ncm = _carregar_refs_co_sefin()

    if ref_cest_ncm is not None:
        ref_cest_ncm = ref_cest_ncm.with_columns([
            pl.col("ncm").map_elements(_limpar_codigo_pontuado, return_dtype=pl.String).alias("_ncm_ref"),
            pl.col("cest").map_elements(_limpar_codigo_pontuado, return_dtype=pl.String).alias("_cest_ref"),
            pl.col("co_sefin").cast(pl.String).alias("_co_sefin_cest_ncm"),
        ]).select(["_ncm_ref", "_cest_ref", "_co_sefin_cest_ncm"])
        df = df.join(ref_cest_ncm, on=["_ncm_ref", "_cest_ref"], how="left")

    if ref_cest is not None:
        ref_cest = ref_cest.with_columns([
            pl.col("cest").map_elements(_limpar_codigo_pontuado, return_dtype=pl.String).alias("_cest_ref"),
            pl.col("co_sefin").cast(pl.String).alias("_co_sefin_cest"),
        ]).select(["_cest_ref", "_co_sefin_cest"])
        df = df.join(ref_cest, on="_cest_ref", how="left")

    if ref_ncm is not None:
        ref_ncm = ref_ncm.with_columns([
            pl.col("ncm").map_elements(_limpar_codigo_pontuado, return_dtype=pl.String).alias("_ncm_ref"),
            pl.col("co_sefin").cast(pl.String).alias("_co_sefin_ncm"),
        ]).select(["_ncm_ref", "_co_sefin_ncm"])
        df = df.join(ref_ncm, on="_ncm_ref", how="left")

    df = df.with_columns(
        pl.coalesce(["_co_sefin_cest_ncm", "_co_sefin_cest", "_co_sefin_ncm"]).alias("co_sefin_item")
    ).drop([c for c in ["_ncm_ref", "_cest_ref", "_co_sefin_cest_ncm", "_co_sefin_cest", "_co_sefin_ncm"] if c in df.columns])

    return df


def gerar_produtos_unidades(cnpj: str, pasta_cnpj: Path | None = None) -> pl.DataFrame | None:
    cnpj = _sanitizar_cnpj(cnpj)
    if pasta_cnpj is None:
        pasta_cnpj = FUNCOES_DIR / "CNPJ" / cnpj

    df_cfop = ler_cfop_mercantil()
    fragmentos = []

    for df in [
        processar_nfe_nfce(_resolver_arquivo(pasta_cnpj, cnpj, "NFe"), cnpj, df_cfop),
        processar_nfe_nfce(_resolver_arquivo(pasta_cnpj, cnpj, "NFCe"), cnpj, df_cfop),
        processar_c170(_resolver_arquivo(pasta_cnpj, cnpj, "c170_simplificada") or _resolver_arquivo(pasta_cnpj, cnpj, "c170"), df_cfop),
        processar_bloco_h(_resolver_arquivo(pasta_cnpj, cnpj, "bloco_h")),
    ]:
        if df is not None and not df.is_empty():
            fragmentos.append(df)

    if not fragmentos:
        rprint("[red]Nenhuma fonte encontrada para gerar produtos_unidades.[/red]")
        return None

    df_total = pl.concat(fragmentos, how="diagonal_relaxed")
    df_total = _aplicar_schema_padrao(df_total)
    df_total = df_total.with_columns([
        pl.col("codigo").map_elements(_limpar_codigo, return_dtype=pl.String).alias("codigo"),
        pl.col("descricao").map_elements(_normalizar_texto, return_dtype=pl.String).alias("descricao"),
        pl.col("descr_compl").map_elements(_normalizar_texto, return_dtype=pl.String).alias("descr_compl"),
        pl.col("tipo_item").map_elements(_normalizar_texto, return_dtype=pl.String).alias("tipo_item"),
        pl.col("ncm").map_elements(_limpar_codigo_pontuado, return_dtype=pl.String).alias("ncm"),
        pl.col("cest").map_elements(_limpar_codigo_pontuado, return_dtype=pl.String).alias("cest"),
        pl.col("gtin").map_elements(_limpar_codigo_pontuado, return_dtype=pl.String).alias("gtin"),
        pl.col("unid").map_elements(_normalizar_texto, return_dtype=pl.String).alias("unid"),
    ])

    df_total = adicionar_co_sefin(df_total)

    for col in COLUNAS_FINAIS:
        if col not in df_total.columns:
            if col in {"compras", "vendas"}:
                df_total = df_total.with_columns(pl.lit(0.0).alias(col))
            else:
                df_total = df_total.with_columns(pl.lit(None, dtype=pl.String).alias(col))

    df_total = df_total.select(COLUNAS_FINAIS)
    pasta_saida = pasta_cnpj / "analises" / "produtos"
    salvar_para_parquet(df_total, pasta_saida, f"produtos_unidades_{cnpj}.parquet")

    rprint(f"[green]produtos_unidades gerado com {len(df_total)} registros.[/green]")
    return df_total


if __name__ == "__main__":
    if len(sys.argv) > 1:
        gerar_produtos_unidades(sys.argv[1])
    else:
        print("Uso: python produtos_unidades.py <cnpj>")
