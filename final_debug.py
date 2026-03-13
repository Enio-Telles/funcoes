import polars as pl
import json

try:
    path = r'c:\Users\03002693901\OneDrive - SECRETARIA DE ESTADO DE FINANCAS\Desenvolvimento\sefin_audit_2\CNPJ\37671507000187\analises\produtos_agregados_37671507000187.parquet'
    df = pl.read_parquet(path)
    
    results = {
        "columns": df.columns,
        "sample": df.head(10).to_dicts()
    }
    
    # Check for same prefix in chave_produto
    df_ext = df.with_columns(
        pl.col("chave_produto").str.replace(r"_[^_]+$", "").alias("codigo_base")
    )
    dup_codes = df_ext.group_by("codigo_base").agg(pl.count().alias("n")).filter(pl.col("n") > 1).head(5)
    
    if dup_codes.height > 0:
        results["identity_separation"] = df_ext.filter(pl.col("codigo_base").is_in(dup_codes["codigo_base"].to_list())).select(["chave_produto", "tipo_item_consenso"]).to_dicts()
    else:
        results["identity_separation"] = "No separation found in sample."

    with open("final_debug.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)
except Exception as e:
    with open("final_debug.json", "w") as f:
        json.dump({"error": str(e)}, f)
