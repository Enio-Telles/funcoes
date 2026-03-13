import polars as pl
from pathlib import Path

path = r"C:\Users\03002693901\OneDrive - SECRETARIA DE ESTADO DE FINANCAS\Desenvolvimento\sefin_audit_2\CNPJ\37671507000187\analises\produtos_agregados_37671507000187.parquet"

try:
    df = pl.read_parquet(path)
    print(f"Total Rows: {df.height}")
    
    # Check for same prefix in chave_produto
    df_ext = df.with_columns(
        pl.col("chave_produto").str.replace(r"_[^_]+$", "").alias("codigo_base")
    )
    dup_codes = df_ext.group_by("codigo_base").agg(pl.count().alias("n")).filter(pl.col("n") > 1).sort("n", descending=True).head(5)
    
    if dup_codes.height > 0:
        print(f"Separation found for {dup_codes.height} codes.")
        codes = dup_codes["codigo_base"].to_list()
        sep = df_ext.filter(pl.col("codigo_base").is_in(codes)).select(["chave_produto", "tipo_item_consenso", "lista_fonte"]).sort("chave_produto")
        for row in sep.to_dicts():
            print(f"Key: {row['chave_produto']} | Tipo: {row['tipo_item_consenso']} | Fontes: {row['lista_fonte']}")
    else:
        print("No separation found in this dataset.")
        print("Sample of keys and types:")
        for row in df.head(10).select(["chave_produto", "tipo_item_consenso"]).to_dicts():
            print(f"Key: {row['chave_produto']} | Tipo: {row['tipo_item_consenso']}")

except Exception as e:
    print(f"Error reading file: {e}")
