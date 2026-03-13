import polars as pl
from pathlib import Path

# Configuração de caminhos para o mock
root = Path(r"c:\Users\03002693901\OneDrive - SECRETARIA DE ESTADO DE FINANCAS\Desenvolvimento\sefin_audit_2")
cnpj = "00000000000000"
dir_parquet = root / "CNPJ" / cnpj / "arquivos_parquet"
dir_parquet.mkdir(parents=True, exist_ok=True)

# 1. Mock de Reg_0200 (Identidade)
# Note: Temos 1 codigo com dois tipos diferentes
df_0200 = pl.DataFrame({
    "cod_item": ["P001", "P001", "P002"],
    "descr_item": ["PRODUTO TESTE A", "PRODUTO TESTE A", "PRODUTO TESTE B"],
    "tipo_item": ["00", "01", "00"],
    "cod_ncm": ["12345678", "12345678", "87654321"],
    "cest": ["1111111", "1111111", "2222222"],
    "cod_barra": ["GTIN001", "GTIN001", "GTIN002"]
})
df_0200.write_parquet(dir_parquet / f"reg_0200_{cnpj}.parquet")

# 2. Mock de C170 (Consumo)
df_c170 = pl.DataFrame({
    "cod_item": ["P001", "P001", "P002"],
    "descr_compl": ["COMPL A", "COMPL A2", "COMPL B"],
    "unid": ["UN", "UN", "KG"]
})
df_c170.write_parquet(dir_parquet / f"c170_{cnpj}.parquet")

# 3. Mock de NFe (Sem tipo_item - deve cair no unificado/Vazio)
df_nfe = pl.DataFrame({
    "co_emitente": [cnpj],
    "prod_cprod": ["P001"],
    "prod_xprod": ["PRODUTO NFE"],
    "prod_ncm": ["12345678"],
    "prod_cest": ["1111111"],
    "prod_ceantrib": ["GTIN001"],
    "prod_ucom": ["UN"]
})
df_nfe.write_parquet(dir_parquet / f"NFe_{cnpj}.parquet")

print(f"Mock data created for CNPJ {cnpj} in {dir_parquet}")
