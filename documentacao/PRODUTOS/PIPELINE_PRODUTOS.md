# Pipeline de Produtos

## Etapas
1. Ingestão e mapeamentos por fonte
   - NFe/NFCe → `mapa_produto_nfe_{cnpj}.parquet`
   - SPED 0200 → `mapa_produto_0200_{cnpj}.parquet`
2. Unificação Master
   - Consolidação e resolução de conflitos, gera `produtos_agregados_{cnpj}.parquet`
   - Flags: `requer_revisao_manual`, `descricoes_conflitantes`, `ncm_consenso`, `cest_consenso`, `gtin_consenso`
3. Revisão Manual (Frontend/API)
   - Listar pendências e detalhes
   - Submeter decisões: unificar, desagregar, ajustar NCM/CEST/GTIN/descrição
4. Aplicar Unificação
   - Executa motor (`unificar_produtos_unidades`) e produz `mapa_auditoria_{cnpj}.parquet`

## Pontos de Integração
- `server/python/routers/analysis.py` (pipeline orquestrado)
- `server/python/routers/produto_unid.py` (rotas de revisão e aplicação)
- `server/python/routers/filesystem.py` (listagem de artefatos)
- `server/python/routers/export.py` (Excel de revisão manual)

## Diagrama
```
[NFe/NFCe]   [SPED 0200]
     \         /
   Mapas por Fonte  →  Unificação Master  →  Revisão Manual  →  Aplicar Unificações  →  Mapas/Auditoria
```
