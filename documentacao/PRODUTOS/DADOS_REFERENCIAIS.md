# Dados Referenciais (NCM/CEST)

## NCM
- Caminho: `referencias/NCM/tabela_ncm.parquet`
- Campos típicos: Codigo_NCM, Capitulo, Descr_Capitulo, Posicao, Descr_Posicao, Descricao, Data_Inicio, Data_Fim, Ato_Legal
- Scripts de apoio: `server/inspect_ncm.py`, `server/diag_ncm.py`, `server/diag_ncm_deep.py`

## CEST
- Caminho: `referencias/CEST/cest.parquet`, `referencias/CEST/segmentos_mercadorias.parquet`
- Relacionamento com NCM: via coluna NCM (normalizada)

## Atualização & Validação
- Periodicidade: conforme publicações oficiais (SEFAZ/Camex)
- Checklist:
  - Verificar presença e esquema das colunas acima
  - Rodar `server/inspect_ncm.py` para inspeção
  - Testar endpoints: `GET /api/python/referencias/ncm/{codigo}` e `GET /api/python/referencias/cest/{codigo}`
