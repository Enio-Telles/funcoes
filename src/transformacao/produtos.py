import polars as pl
import unicodedata
import re

def normalize_description(text: str | None) -> str:
    """
    Remove acentos, espaços extras e converte para MAIÚSCULO.
    """
    if text is None:
        return ""
    # Remover acentos
    normalized = unicodedata.normalize("NFKD", str(text))
    text = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    # Converter para MAIÚSCULO e remover espaços extras
    text = text.upper().strip()
    # Substituir múltiplos espaços por um só
    text = re.sub(r"\s+", " ", text)
    return text

def gerar_tabela_produtos_normalizados(df_unidades: pl.DataFrame) -> pl.DataFrame:
    """
    Objetivo: Gerar a tabela de produtos normalizados e únicos.
    Campos: chave_produto, descricao_normalizada, descricao (lista), etc.
    """
    if df_unidades.is_empty():
        return pl.DataFrame()

    # Adicionar coluna de descrição normalizada
    # Nota: Polars .map_elements pode ser lento, mas para strings complexas é seguro.
    # Alternativa mais rápida se possível: pl.col("descricao").str.to_uppercase()...
    df_norm = df_unidades.with_columns(
        pl.col("descricao")
        .fill_null("")
        .map_elements(normalize_description, return_dtype=pl.Utf8)
        .alias("descricao_normalizada")
    )

    # Agrupar por descricao_normalizada
    # Coletar listas de atributos para rastreabilidade
    df_produtos = (
        df_norm
        .group_by("descricao_normalizada")
        .agg([
            pl.col("descricao").unique().alias("lista_desc"),
            pl.col("codigo").unique().alias("lista_codigos"),
            pl.col("ncm").unique().alias("lista_ncm"),
            pl.col("cest").unique().alias("lista_cest"),
            pl.col("gtin").unique().alias("lista_gtin"),
            pl.col("unid").unique().alias("lista_unid"),
            pl.col("fonte").unique().alias("lista_fontes"),
            # Atributo 'descricao' principal (o mais frequente ou o primeiro)
            pl.col("descricao").mode().first().alias("descricao"),
        ])
        .sort("descricao_normalizada")
    )

    # Gerar chave_produto determinística (id_produto_1, ...)
    df_produtos = df_produtos.with_columns(
        (pl.lit("id_produto_") + (pl.int_range(0, pl.len()) + 1).cast(pl.Utf8)).alias("chave_produto")
    )

    return df_produtos
