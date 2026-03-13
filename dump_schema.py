import polars as pl
import json
from pathlib import Path

path = r"C:\Users\03002693901\OneDrive - SECRETARIA DE ESTADO DE FINANCAS\Desenvolvimento\sefin_audit_2\CNPJ\37671507000187\analises\produtos_agregados_37671507000187.parquet"

try:
    lf = pl.scan_parquet(path)
    schema = {k: str(v) for k, v in lf.collect_schema().items()}
    with open('schema_final.json', 'w') as f:
        json.dump(schema, f, indent=4)
except Exception as e:
    with open('schema_final.json', 'w') as f:
        json.dump({"error": str(e)}, f, indent=4)
