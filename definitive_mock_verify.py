import polars as pl

path = r"C:\Users\03002693901\OneDrive - SECRETARIA DE ESTADO DE FINANCAS\Desenvolvimento\sefin_audit_2\CNPJ\00000000000000\analises\produtos_agregados_00000000000000.parquet"

try:
    df = pl.read_parquet(path)
    print(f"Total rows: {df.height}")
    
    # Filtrar por codigo P001 (que deve ter 3 tipos: 00, 01, (Vazio))
    df_p001 = df.filter(pl.col('chave_produto').str.starts_with('P001')).select([
        'chave_produto', 'tipo_item_consenso', 'ncm_consenso', 'lista_fonte'
    ]).sort('chave_produto')
    
    # Imprimir como dicionários para evitar problemas de encoding com caracteres de tabela
    print("\nRows for P001 (Should be 3):")
    for row in df_p001.to_dicts():
        print(row)
    
    expected_rows = 3
    if df_p001.height == expected_rows:
        print("\nSUCCESS: Identity separation verified!")
    else:
        print(f"\nFAILURE: Expected {expected_rows} rows for P001, but found {df_p001.height}.")
        
except Exception as e:
    print(f"Error during verification: {e}")
