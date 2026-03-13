# Relatórios — Produtos

## Excel de Revisão Manual
- Gerado via rota de exportação (ver `server/python/routers/export.py`)
- Conteúdo típico:
  - Lista de `chave_produto` com sinalização `requer_revisao_manual`
  - Atributos atuais e sugeridos (NCM/CEST/GTIN/descrição)
- Uso: analistas preenchem ajustes e o sistema aplica via endpoints de revisão

## Mapa de Auditoria
- `mapa_auditoria_{cnpj}.parquet` consolidando decisões e histórico
