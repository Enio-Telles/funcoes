# Troubleshooting — Produtos

## Erros Comuns
- Arquivo `produtos_agregados_{cnpj}.parquet` não encontrado
  - Rodar unificação primeiro (pipeline em `routers/analysis.py` ou endpoint adequado)
- Colunas faltantes (ex.: `tipo_item_consenso`)
  - Verificar scripts auxiliares: `verify_vazios.py`, `verify_identity.py`, `verify_attributes.py`
- Duplicidades em merges
  - Validar chaves (ex.: `chave_produto`) e aplicar `unique` conforme necessário

## Dicas de Validação
- Conferir outputs em `CNPJ/{cnpj}/analises/`
- Usar endpoints `/produtos/detalhes-codigo` e `/produtos/detalhes-multi-codigo` para inspecionar origens
