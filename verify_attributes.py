import polars as pl
from pathlib import Path

path = Path(r'c:\Users\03002693901\OneDrive - SECRETARIA DE ESTADO DE FINANCAS\Desenvolvimento\sefin_audit_2\CNPJ\37671507000187\analises\produtos_agregados_37671507000187.parquet')
df = pl.read_parquet(path)
row = df.filter(pl.col('chave_produto') == '11_agr').to_dicts()[0]

print("--- VERIFICAÇÃO ATRIBUTOS 11_agr ---")
for k in ['chave_produto', 'lista_codigos', 'lista_ncm', 'lista_fonte', 'lista_descricao']:
    print(f"{k}: {row[k]}")
print("-------------------------------------")
