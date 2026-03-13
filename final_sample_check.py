import polars as pl
import json

path = r"C:\Users\03002693901\OneDrive - SECRETARIA DE ESTADO DE FINANCAS\Desenvolvimento\sefin_audit_2\CNPJ\37671507000187\analises\produtos_agregados_37671507000187.parquet"

try:
    df = pl.read_parquet(path)
    sample = df.head(10).select(["chave_produto", "tipo_item_consenso", "lista_fonte"]).to_dicts()
    with open('final_sample.json', 'w') as f:
        json.dump({"total_rows": df.height, "sample": sample}, f, indent=4)
except Exception as e:
    with open('final_sample.json', 'w') as f:
        json.dump({"error": str(e)}, f, indent=4)
