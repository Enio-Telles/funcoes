import polars as pl
from typing import Optional

def definir_unid_ref(df_unidades: pl.DataFrame) -> str:
    """
    Define a unidade de referência (modal) para cada chave_produto.
    """
    if df_unidades.is_empty():
        return ""
    
    # Unidade que mais ocorre nas tabelas base
    # (Poderia ser por produto, mas aqui vamos buscar a global ou usar a moda do produto)
    res = df_unidades.group_by("unid").count().sort("count", descending=True)
    if not res.is_empty():
        return res[0, "unid"]
    return "UN"

def calcular_precos_medios(df_unidades: pl.DataFrame) -> pl.DataFrame:
    """
    Calcula o preço médio de compra por unidade para cada produto.
    """
    if df_unidades.is_empty():
        return pl.DataFrame()

    # Filtrar apenas compras (C170/NFe com is_compra=True)
    df_compras = df_unidades.filter((pl.col("is_compra") == True) & (pl.col("quantidade") > 0))
    
    if df_compras.is_empty():
        return pl.DataFrame()

    # Preço Médio = SOMA(valor_liquido) / SOMA(quantidade)
    df_precos = (
        df_compras
        .group_by(["id_produto", "unid"])
        .agg([
            pl.col("valor_liquido").sum().alias("total_valor"),
            pl.col("quantidade").sum().alias("total_qtd"),
        ])
        .with_columns(
            (pl.col("total_valor") / pl.col("total_qtd")).alias("preco_medio")
        )
    )
    return df_precos

def calcular_fatores_conversao(df_unidades: pl.DataFrame, df_final: pl.DataFrame) -> pl.DataFrame:
    """
    Calcula a relação entre diferentes unidades de medida do mesmo produto.
    Fator = Preço Médio Compra da Unidade / Preço Médio Compra da Unid Ref
    """
    if df_unidades.is_empty():
        return pl.DataFrame()

    # Precisamos de um mapeamento entre id_produto e id_agrupado do df_final
    # mas para simplificar, vamos usar as unidades diretamente.
    
    # 1. Definir Preço Médio Global por Unidade (como fallback se por produto não houver)
    # ou preferencialmente por 'Natureza do Produto'. 
    # Dado que o fator é por produto:
    
    df_precos = (
        df_unidades
        .filter((pl.col("valor_liquido") > 0) & (pl.col("quantidade") > 0))
        .group_by("unid")
        .agg([
            (pl.col("valor_liquido").sum() / pl.col("quantidade").sum()).alias("preco_medio_unid")
        ])
    )
    
    if df_precos.is_empty():
        return pl.DataFrame()

    # 2. Definir unid_ref (Moda)
    unid_ref = definir_unid_ref(df_unidades)
    
    # Preço da Unidade de Referência
    preco_ref_row = df_precos.filter(pl.col("unid") == unid_ref)
    if preco_ref_row.is_empty():
        # Se não tiver preço para a moda, pega a primeira unidade com preço
        preco_ref = df_precos[0, "preco_medio_unid"]
        unid_ref = df_precos[0, "unid"]
    else:
        preco_ref = preco_ref_row[0, "preco_medio_unid"]

    # 3. Calcular Fator
    df_fatores = df_precos.with_columns([
        pl.lit(unid_ref).alias("unid_ref"),
        (pl.col("preco_medio_unid") / preco_ref).alias("fator")
    ])

    return df_fatores
