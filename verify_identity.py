import polars as pl
import json
from pathlib import Path
import config

try:
    _, dir_analises, _ = config.obter_diretorios_cnpj('37671507000187')
    path = dir_analises / f"produtos_agregados_37671507000187.parquet"
    
    if not path.exists():
        results = {"error": f"Path does not exist: {path}"}
    else:
        df = pl.read_parquet(str(path))
        
        # Check for composite key separation
        # We want to see if a single 'codigo' resulted in multiple 'chave_produto' entries
        df_ext = df.with_columns(
            pl.col("chave_produto").str.replace(r"_[^_]+$", "").alias("codigo_base")
        )
        
        # Identity counts per base code
        ident_counts = df_ext.group_by("codigo_base").agg(pl.count().alias("n_tipos")).filter(pl.col("n_tipos") > 1)
        
        separation_data = []
        if ident_counts.height > 0:
            codes = ident_counts.head(5)["codigo_base"].to_list()
            sep_rows = df_ext.filter(pl.col("codigo_base").is_in(codes)).select(["chave_produto", "tipo_item_consenso", "lista_fonte"]).sort("chave_produto")
            separation_data = sep_rows.to_dicts()
        
        results = {
            "columns": df.columns,
            "total_rows": df.height,
            "has_tipo_item_consenso": "tipo_item_consenso" in df.columns,
            "identity_separation_found": ident_counts.height > 0,
            "separation_examples": separation_data,
            "sample": df.head(5).to_dicts()
        }

    with open("final_verification.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)
except Exception as e:
    with open("final_verification.json", "w", encoding="utf-8") as f:
        json.dump({"error": str(e)}, f, indent=4)
