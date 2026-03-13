import polars as pl
try:
    path = r'c:\Users\03002693901\OneDrive - SECRETARIA DE ESTADO DE FINANCAS\Desenvolvimento\sefin_audit_2\CNPJ\37671507000187\analises\produtos_agregados_37671507000187.parquet'
    df = pl.read_parquet(path)
    
    # Procura por códigos que tenham mais de uma chave_produto (ou seja, diferentes tipos para o mesmo código)
    df_counts = df.group_by("codigo").agg(pl.count().alias("n_tipos")).filter(pl.col("n_tipos") > 1)
    
    if df_counts.height > 0:
        codigos = df_counts.head(5)["codigo"].to_list()
        print(f"Encontrados {df_counts.height} códigos com múltiplos tipos.")
        print("Exemplos de separação:")
        subset = df.filter(pl.col("codigo").is_in(codigos)).select(["chave_produto", "codigo", "tipo_item_consenso", "lista_fonte"]).sort("codigo")
        for row in subset.to_dicts():
            print(f"Chave: {row['chave_produto']} | Cod: {row['codigo']} | Tipo: {row['tipo_item_consenso']} | Fontes: {row['lista_fonte']}")
    else:
        print("Nenhum código com múltiplos tipos encontrado na amostra.")
        print("Amostra Geral:")
        subset = df.head(10).select(["chave_produto", "codigo", "tipo_item_consenso", "lista_fonte"])
        for row in subset.to_dicts():
            print(f"Chave: {row['chave_produto']} | Cod: {row['codigo']} | Tipo: {row['tipo_item_consenso']} | Fontes: {row['lista_fonte']}")

except Exception as e:
    print(f"Erro: {e}")
