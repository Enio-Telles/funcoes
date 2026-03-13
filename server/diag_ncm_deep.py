import polars as pl
import json

path = r'c:\Users\eniot\OneDrive - SECRETARIA DE ESTADO DE FINANCAS\Desenvolvimento\sefin_audit_2\referencias\NCM\tabela_ncm.parquet'
df = pl.read_parquet(path)

# 1. Get all 4-digit codes
four_digits = df.filter(pl.col("Codigo_NCM").str.replace_all(r"[^0-9]", "").str.len_chars() == 4).head(100)

# 2. Search for any row containing spirits-related terms in Descricao
spirits = df.filter(pl.col("Descricao").str.contains("(?i)Aguardentes|(?i)Uísque")).head(10)

# 3. Specifically look for 2208 again with a broader filter
broad_2208 = df.filter(pl.col("Codigo_NCM").str.contains("2208")).head(20)

output = {
    "four_digits_sample": four_digits.to_dicts(),
    "spirits_sample": spirits.to_dicts(),
    "broad_2208": broad_2208.to_dicts()
}

with open('ncm_debug_deep.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print("Deep Diagnostic Done")
