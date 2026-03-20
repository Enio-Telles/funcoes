import polars as pl
from typing import Optional, List

def determinar_atributos_padrao(df_itens: pl.DataFrame) -> pl.DataFrame:
    """
    Lógica 'Ganha quem corre mais' para definir atributos padrão (NCM, CEST, GTIN).
    1º Maior quantidade de campos preenchidos.
    2º Tamanho da descrição.
    3º Frequência (Modal).
    """
    if df_itens.is_empty():
        return pl.DataFrame()

    # Calcular heurísticas para cada linha original
    df_heuristica = df_itens.with_columns([
        # Contagem de campos preenchidos (NCM, CEST, GTIN)
        (
            pl.col("ncm").is_not_null().cast(pl.Int32) + 
            pl.col("cest").is_not_null().cast(pl.Int32) + 
            pl.col("gtin").is_not_null().cast(pl.Int32)
        ).alias("score_preenchimento"),
        
        # Tamanho da descrição
        pl.col("descricao").str.len_chars().fill_null(0).alias("score_tamanho")
    ])

    return df_heuristica

def produtos_agrupados(df_produtos: pl.DataFrame, df_manual: Optional[pl.DataFrame] = None) -> pl.DataFrame:
    """
    Gera a tabela final unindo produtos com agrupamentos manuais.
    df_manual deve conter: id_agrupado, lista_chave_produto
    """
    if df_produtos.is_empty():
        return pl.DataFrame()

    # Se não houver manual, cada produto é seu próprio grupo
    if df_manual is None or df_manual.is_empty():
        df_final = df_produtos.with_columns([
            pl.col("chave_produto").alias("id_agrupado"),
            pl.lit(False).alias("is_manual")
        ])
    else:
        # Explodir manual para facilitar join
        df_manual_exploded = df_manual.explode("lista_chave_produto")
        
        # Join com produtos
        df_final = df_produtos.join(
            df_manual_exploded,
            left_on="chave_produto",
            right_on="lista_chave_produto",
            how="left"
        ).with_columns([
            # Se não estiver no manual, mantém o id original
            pl.coalesce(["id_agrupado", "chave_produto"]).alias("id_agrupado"),
            pl.col("id_agrupado").is_not_null().alias("is_manual")
        ])

    # Agregar por id_agrupado e aplicar heurística de atributos padrão
    # Para simplificar, vamos explodir as listas originais para recalcular a moda/heurística
    # ou usar a lógica de agregação do Polars.
    
    # Nota: A especificação pede para recalcular caso os agrupamentos sejam revisados.
    
    df_resultado = (
        df_final
        .group_by("id_agrupado")
        .agg([
            pl.col("chave_produto").alias("lista_chave_produto"),
            pl.col("descricao").mode().first().alias("descr_padrao"), # Simplificando moda
            pl.col("lista_codigos").flatten().unique().alias("lista_codigos"),
            pl.col("lista_ncm").flatten().unique().alias("lista_ncm"),
            pl.col("lista_unid").flatten().unique().alias("lista_unidades"),
            # Heurística para NCM/CEST/GTIN Padrão (simplificado para Moda por enquanto)
            pl.col("lista_ncm").flatten().mode().first().alias("ncm_padrao"),
            pl.col("lista_cest").flatten().mode().first().alias("cest_padrao"),
            pl.col("lista_gtin").flatten().mode().first().alias("gtin_padrao"),
        ])
    )

    return df_resultado
