import polars as pl
from pathlib import Path
from typing import Optional

# Mapeamentos de Colunas por Fonte (Ref: Diretrizes de Auditoria)
MAP_NFE = {
    "prod_cprod": "codigo",
    "prod_xprod": "descricao",
    "prod_ncm": "ncm",
    "prod_cest": "cest",
    "prod_ceantrib": "gtin",
    "prod_ucom": "unid",
    "prod_vprod": "valor_bruto",
    "prod_qcom": "quantidade",
    "prod_vfrete": "valor_frete",
    "prod_vseg": "valor_seguro",
    "prod_voutro": "valor_outro",
    "prod_vdesc": "valor_desconto",
    "co_cfop": "cfop"
}

MAP_C170 = {
    "cod_item": "codigo",
    "descr_item": "descricao",
    "cod_ncm": "ncm",
    "cod_barra": "gtin",
    "unid": "unid",
    "vl_item": "valor_bruto",
    "qtd": "quantidade",
    "cfop": "cfop"
}

MAP_BLOCO_H = {
    "codigo_produto": "codigo",
    "descricao_produto": "descricao",
    "cod_ncm": "ncm",
    "cod_barra": "gtin",
    "unidade_medida": "unid",
    "valor_item": "valor_bruto",
    "quantidade": "quantidade"
}

def gerar_tabela_produtos_unidades(
    cnpj: str,
    df_c170: Optional[pl.DataFrame] = None,
    df_nfe_itens: Optional[pl.DataFrame] = None,
    df_nfce_itens: Optional[pl.DataFrame] = None,
    df_bloco_h: Optional[pl.DataFrame] = None,
    df_cfop_ref: Optional[pl.DataFrame] = None
) -> pl.DataFrame:
    """
    Objetivo: Gerar a tabela base de movimentações por unidade.
    Standardiza colunas e classifica movimentações entre Compras e Vendas.
    """
    fragmentos = []

    # 1. Processar C170 (EFD) - Foco em Compras
    if df_c170 is not None:
        df = df_c170.rename({c: n for c, n in MAP_C170.items() if c in df_c170.columns})
        df = df.with_columns([
            pl.lit("C170").alias("fonte"),
            pl.col("valor_bruto").fill_null(0).alias("valor_liquido"), # C170 vl_item já costuma ser líq ou bruto dependendo da EFD
        ])
        # Lógica de Compras: ind_oper = 0 (Entrada)
        if "ind_oper" in df.columns:
            df = df.with_columns(
                pl.when(pl.col("ind_oper") == "0").then(pl.lit(True)).otherwise(pl.lit(False)).alias("is_compra")
            )
        else:
            df = df.with_columns(pl.lit(True).alias("is_compra"))
            
        fragmentos.append(df.select(pl.all()))

    # 2. Processar NFe e NFCe - Foco em Vendas
    for df_raw, nome_fonte in [(df_nfe_itens, "NFe"), (df_nfce_itens, "NFCe")]:
        if df_raw is not None:
            df = df_raw.rename({c: n for c, n in MAP_NFE.items() if c in df_raw.columns})
            
            # Cálculo de Preço de Venda Líquido
            cols_fin = ["valor_frete", "valor_seguro", "valor_outro", "valor_desconto"]
            for col in cols_fin:
                if col not in df.columns:
                    df = df.with_columns(pl.lit(0).alias(col))
            
            df = df.with_columns(
                (pl.col("valor_bruto").fill_null(0) + 
                 pl.col("valor_frete").fill_null(0) + 
                 pl.col("valor_seguro").fill_null(0) + 
                 pl.col("valor_outro").fill_null(0) - 
                 pl.col("valor_desconto").fill_null(0)).alias("valor_liquido")
            )
            
            # Identificar Saídas (Vendas do CNPJ)
            if "co_emitente" in df.columns:
                df = df.with_columns(
                    pl.when(pl.col("co_emitente") == cnpj).then(pl.lit(False)).otherwise(pl.lit(True)).alias("is_venda")
                )
            else:
                df = df.with_columns(pl.lit(True).alias("is_venda"))
            
            df = df.with_columns(pl.lit(nome_fonte).alias("fonte"))
            fragmentos.append(df.select(pl.all()))

    # 3. Processar Bloco H (Inventário)
    if df_bloco_h is not None:
        df = df_bloco_h.rename({c: n for c, n in MAP_BLOCO_H.items() if c in df_bloco_h.columns})
        df = df.with_columns([
            pl.lit("Bloco H").alias("fonte"),
            pl.col("valor_bruto").alias("valor_liquido"),
            pl.lit(False).alias("is_compra"),
            pl.lit(False).alias("is_venda")
        ])
        fragmentos.append(df.select(pl.all()))

    if not fragmentos:
        return pl.DataFrame()

    # Unir todos os fragmentos
    df_unidades = pl.concat(fragmentos, how="diagonal_relaxed")

    # Enriquecer com CFOP Ref se disponível (para validar operacao_mercantil = 'X')
    if df_cfop_ref is not None and "cfop" in df_unidades.columns:
        df_unidades = df_unidades.join(
            df_cfop_ref.select(["cfop", "operacao_mercantil"]),
            on="cfop",
            how="left"
        )
        # Refinar is_compra: CFOP mercantil 'X'
        df_unidades = df_unidades.with_columns(
            pl.when(pl.col("operacao_mercantil") == "X").then(pl.col("is_compra")).otherwise(pl.lit(False)).alias("is_compra")
        )

    return df_unidades
