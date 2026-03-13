# API e Scripts (Produtos)

## Endpoints Produtos
- GET `/api/python/produtos/revisao-manual?cnpj=...`
- GET `/api/python/produtos/detalhes-codigo?cnpj=...&codigo=...`
- POST `/api/python/produtos/detalhes-multi-codigo`
- POST `/api/python/produtos/revisao-manual/submit`
- POST `/api/python/produtos/resolver-manual-unificar`
- POST `/api/python/produtos/resolver-manual-desagregar`

## Endpoints Referências
- GET `/api/python/referencias/ncm/{codigo}`
- GET `/api/python/referencias/cest/{codigo}`

## Exportação
- Excel de revisão manual via `server/python/routers/export.py`

## Exemplos (cURL)
```bash
curl "http://localhost:8001/api/python/produtos/revisao-manual?cnpj=37671507000187"
```
```bash
curl -X POST "http://localhost:8001/api/python/produtos/revisao-manual/submit" \
  -H "Content-Type: application/json" \
  -d '{"cnpj":"37671507000187","decisoes":[{"acao":"unificar","codigo":"P001","ncm":"12345678"}]}'
```
