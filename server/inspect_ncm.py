import polars as pl
import json
import os

path = r'c:\Users\eniot\OneDrive - SECRETARIA DE ESTADO DE FINANCAS\Desenvolvimento\sefin_audit_2\referencias\NCM\tabela_ncm.parquet'
if not os.path.exists(path):
    print(f"File not found: {path}")
    exit(1)

df = pl.read_parquet(path).head(10000) # limit for safety

# Search for 2208
res2208 = df.filter(pl.col("Codigo_NCM").str.replace_all(r"[^0-9]", "").str.starts_with("2208")).head(20)

output = {
    "schema": str(df.schema),
    "count": len(df),
    "sample_2208": res2208.to_dicts()
}

with open('ncm_inspect.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print("Done")
