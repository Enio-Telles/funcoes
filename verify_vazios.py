import polars as pl
try:
    path = r'c:\Users\03002693901\OneDrive - SECRETARIA DE ESTADO DE FINANCAS\Desenvolvimento\sefin_audit_2\CNPJ\37671507000187\analises\produtos_agregados_37671507000187.parquet'
    df = pl.read_parquet(path)
    
    with open("vazios_check.txt", "w", encoding="utf-8") as f:
        f.write("Amostra de chave_produto e tipo_item\n")
        f.write("="*40 + "\n")
        
        # Amostra geral
        subset = df.head(10).select(["chave_produto", "tipo_item_consenso"])
        for row in subset.to_dicts():
            f.write(f"Key: {row['chave_produto']} | Tipo: {row['tipo_item_consenso']}\n")
            
        f.write("\nBusca por separação de código idêntico (via prefixo da chave):\n")
        # Extrai o código da chave (antes do último _)
        df_ext = df.with_columns(
            pl.col("chave_produto").str.replace(r"_[^_]+$", "").alias("codigo_base")
        )
        counts = df_ext.group_by("codigo_base").agg(pl.count().alias("n")).filter(pl.col("n") > 1).head(5)
        
        if counts.height > 0:
            codes = counts["codigo_base"].to_list()
            sep = df_ext.filter(pl.col("codigo_base").is_in(codes)).select(["chave_produto", "tipo_item_consenso"]).sort("chave_produto")
            for row in sep.to_dicts():
                f.write(f"Key: {row['chave_produto']} | Tipo: {row['tipo_item_consenso']}\n")
        else:
            f.write("Nenhum código com múltiplos tipos encontrado na amostra global.\n")
            
except Exception as e:
    with open("vazios_check.txt", "w") as f: f.write(str(e))
