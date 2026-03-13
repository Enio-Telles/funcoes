# Checklist de Implementação - Quick Start

Use este checklist para implementar as correções e melhorias. ✅ = completo, ⏳ = em progresso, ❌ = não iniciado

---

## SPRINT 1: Correções Críticas (48h)

### Dia 1: Fix Polars + Error Handling

- [ ] **TASK 1.1**: Localizar e corrigir Polars `.list.lengths()` deprecation
  - [ ] Abrir arquivo `cruzamentos/agrupamento_produtos.py`
  - [ ] Procurar por `.list.lengths()`
  - [ ] Substituir por `.list.len()`
  - [ ] Testar com CNPJ `37671507000187`
  - [ ] Validar HTTP 200 (sem erro 500)
  - **Tempo**: 30 min

- [ ] **TASK 1.2**: Criar classes de erro customizadas
  - [ ] Criar `server/python/errors.py` (copiar template)
  - [ ] Implementar `AuditError`, `OracleConnectionError`, `DataValidationError`, `ParquetProcessingError`
  - [ ] Adicionar método `.to_dict()` para JSON serialization
  - [ ] Testes: `python -m pytest server/python/errors.py`
  - **Tempo**: 1h

- [ ] **TASK 1.3**: Atualizar api.py com error handling
  - [ ] Abrir `server/python/api.py`
  - [ ] Importar classes de erro: `from errors import AuditError, DataValidationError`
  - [ ] Atualizar função `agrupar_produtos`:
    - [ ] Adicionar validação CNPJ com DataValidationError
    - [ ] Try/catch com AuditError ao invés de Exception genérica
    - [ ] Retornar `error.to_dict()` ao invés de `str(e)`
  - [ ] Remover credenciais de logs
    - [ ] Procurar por `logger.info` ou `print` que mencione `password` ou `user`
    - [ ] Substituir por logs seguros (ex: `logger.info(f"Conectando a {host}")`)
  - [ ] Testes: Chamar API com CNPJ inválido, verificar erro 400 estruturado
  - **Tempo**: 1.5h

- [ ] **TASK 1.4**: Atualizar respostas de erro
  - [ ] Verificar todas as funções da API Python
  - [ ] Garantir que `except Exception` sempre retorna `error: {...}` estruturado
  - [ ] Não retornar `str(error)` raw
  - **Tempo**: 45 min

**Dia 1 Total**: 3h 45 min | **Status**: ⏳ TODO

---

### Dia 2: Validação com Zod

- [ ] **TASK 2.1**: Instalar Zod
  - [ ] `npm install zod`
  - [ ] Verificar: `npm list zod`
  - **Tempo**: 5 min

- [ ] **TASK 2.2**: Criar schemas compartilhados
  - [ ] Criar arquivo `shared/schemas.ts` (copiar template)
  - [ ] Implementar:
    - [ ] `CnpjSchema` - valida 14 dígitos
    - [ ] `OracleCredsSchema` - host, port, user, pass
    - [ ] `AgrupamentoProdutosRequestSchema` - request agrupamento
    - [ ] `RefazerMovimentosRequestSchema` - request refazer
    - [ ] `ApiResponseSchema` - resposta genérica
  - [ ] TypeScript check: `npm run check`
  - [ ] Verificar tipos aparecem corretamente
  - **Tempo**: 1h

- [ ] **TASK 2.3**: Implementar middleware de validação
  - [ ] Criar `server/_core/middlewares.ts` com `validateRequest(schema)`
  - [ ] Implementar error handling com mensagens claras
  - [ ] Retornar HTTP 400 para validação falha
  - **Tempo**: 45 min

- [ ] **TASK 2.4**: Aplicar validação em routers críticos
  - [ ] Abrir `server/routers.ts`
  - [ ] Adicionar middleware em:
    - [ ] `/produtos/agrupamento` → `AgrupamentoProdutosRequestSchema`
    - [ ] `/extraction/oracle` → `OracleCredsSchema`
    - [ ] `/produtos/refazer` → `RefazerMovimentosRequestSchema`
  - [ ] Testes: Chamar com dados inválidos, verificar 400
  - **Tempo**: 1h

- [ ] **TASK 2.5**: Atualizar TypeScript types
  - [ ] Remover `any[]` do pythonApi.ts
  - [ ] Usar schemas para type narrowing
  - [ ] `npm run check` sem warnings
  - **Tempo**: 30 min

**Dia 2 Total**: 3h 20 min | **Status**: ⏳ TODO

**SPRINT 1 TOTAL**: ~7h (Fácil de caber em 2 dias) ✅

---

## SPRINT 2: Funcionalidades (1 semana)

### **TASK 3.1**: Implementar Refazer Movimentos

- [ ] Criar `cruzamentos/refazer_movimentos.py`
  - [ ] Funcão `refazer_nfe(cnpj, mapa, output_dir) -> dict`
  - [ ] Funcão `refazer_c170(cnpj, mapa, output_dir) -> dict`
  - [ ] Funcão `refazer_nfce(cnpj, mapa, output_dir) -> dict`
  - [ ] Função `executar_refazer_movimentos(cnpj, output_dir) -> dict`
  - [ ] Adicionar versionamento automático (timestamp)
  - [ ] Testes unitários: `pytest cruzamentos/test_refazer.py`
  - **Tempo**: 3h

- [ ] Expor endpoint em `server/python/api.py`
  - [ ] `@app.post("/api/python/produtos/refazer")`
  - [ ] Validar CNPJ com `DataValidationError`
  - [ ] Chamar `executar_refazer_movimentos`
  - [ ] Retornar resultado estruturado
  - [ ] Testar com curl
  - **Tempo**: 45 min

- [ ] Atualizar frontend `AnaliseAgrupamentoProdutos.tsx`
  - [ ] Adicionar button "Processar Tudo"
  - [ ] Chamar endpoint `/api/python/produtos/refazer`
  - [ ] Mostrar progresso com toast
  - [ ] Desabilitar durante processamento
  - [ ] Testar clique no botão
  - **Tempo**: 1h

**TASK 3.1 Total**: 4h 45 min | **Status**: ⏳ TODO

---

### **TASK 3.2**: Adicionar Testes Integração

- [ ] Criar `server/test/agrupamento.test.ts`
  - [ ] Test: CNPJ válido → sucesso
  - [ ] Test: CNPJ inválido → errro 400
  - [ ] Test: CNPJ não existe → erro 404
  - [ ] Rodar: `npm run test`
  - **Tempo**: 45 min

- [ ] Criar `cruzamentos/test_refazer.py`
  - [ ] Test: `test_refazer_com_mapa_valido()`
  - [ ] Test: `test_refazer_com_cnpj_invalido()`
  - [ ] Test: `test_arquivos_versionados()`
  - [ ] Rodar: `pytest cruzamentos/test_refazer.py -v`
  - **Tempo**: 1h

**TASK 3.2 Total**: 1h 45 min | **Status**: ⏳ TODO

**SPRINT 2 TOTAL**: ~6.5h (1 dev == 1 dia full-time) ✅

---

## SPRINT 3: Qualidade e Cleanup (1-2 semanas)

- [ ] **TASK 4.1**: Remover arquivos debug/temporários
  - [ ] Deletar: `0_apagar/`, `*-Enio.*`, `*_debug.*`
  - [ ] Manter apenas essencial
  - **Tempo**: 15 min

- [ ] **TASK 4.2**: Adicionar mais testes
  - [ ] Unit tests: Validators (Zod schemas)
  - [ ] Integration tests: Oracle connection
  - [ ] E2E test: Extração → Agrupamento → Refazer → Exportação
  - [ ] Target: 70%+ cobertura em código crítico
  - **Tempo**: 3h

- [ ] **TASK 4.3**: Setup Observability
  - [ ] Instalar OpenTelemetry: `npm install @opentelemetry/api`
  - [ ] Logger estruturado em JSON (ex: `winston`)
  - [ ] Registrar: timestamps, cnpj, status, duração
  - **Tempo**: 2h

- [ ] **TASK 4.4**: Documentação
  - [ ] Atualizar README.md com novas features
  - [ ] Adicionar exemplos de uso de validação
  - [ ] Documentar errors customizados (onde encontrado no código)
  - [ ] Manter ARCHITECTURE.md sincronizado
  - **Tempo**: 1.5h

- [ ] **TASK 4.5**: Review Final
  - [ ] `npm run check` - zero TypeScript warnings
  - [ ] `npm run build` - build sem erros
  - [ ] `npm run test` - todos tests passando
  - [ ] `npm run format` - código formatado
  - [ ] Rodar servidor: `npm run dev` - sem warnings
  - [ ] Testar API (curl) - respostas esperadas
  - **Tempo**: 1h

**SPRINT 3 TOTAL**: ~7.5h (1 dev == 1 dia) ✅

---

## Validação Final ✅

Antes de considerar DONE, executar esta sequência:

```bash
# 1. Limpar e instalar
rm -rf node_modules
npm install
npm run build

# 2. Type checking
npm run check  # Zero errors

# 3. Formatação
npm run format

# 4. Testes
npm run test   # Todos passando

# 5. Testes integração (local)
pytest cruzamentos/test_refazer.py -v

# 6. API Test (Terminal 1)
npm run dev
# Aguardar "Server running on :3000"

# (Terminal 2)
# Test validação CNPJ inválido
curl -X POST http://localhost:3000/api/trpc/extracaoProdutos.agrupamento \
  -H "Content-Type: application/json" \
  -d '{"cnpj": "invalid"}'
# Esperado: 400 Bad Request com erro estruturado

# Test CNPJ válido (requer Oracle)
curl -X POST http://localhost:8001/api/python/produtos/agrupamento \
  -H "Content-Type: application/json" \
  -d '{"cnpj": "37671507000187"}'
# Esperado: 200 OK com resultado JSON

# Test refazer
curl -X POST http://localhost:8001/api/python/produtos/refazer \
  -H "Content-Type: application/json" \
  -d '{"cnpj": "37671507000187"}'
# Esperado: 200 OK com arquivos versionados criados

# 7. Verificar logs (sem credenciais!)
tail -f server/logs/*.log
# Não deve aparecer: password, user details, ou credenciais Oracle
```

### Checklist de Aceitação Final

- [ ] ✅ Polars API atualizada (.list.len() funciona)
- [ ] ✅ HTTP 200 em agrupamento (sem erro 500)
- [ ] ✅ Credenciais NUNCA nos logs
- [ ] ✅ Validação Zod em routers críticos
- [ ] ✅ Error responses com código + contexto
- [ ] ✅ Refazer movimentos cria arquivos
- [ ] ✅ Testes: 50+ tests, 70%+ cobertura crítica
- [ ] ✅ Zero TypeScript warnings
- [ ] ✅ Build sem erros
- [ ] ✅ README.md + documentação atualizado

---

## Roadmap Timeline

```
MON (14/03)    TUE (15/03)    WED (16/03)    THU (17/03)    FRI (18/03)
Sprint 1.1     Sprint 1.1     Sprint 1.2     Sprint 1.2     
(Polars fix)   (finish)       (Zod)          (finish)       
 3h dev         2h           3.5h           1.5h            Testing
                                                            8h total

WEEK 2: Sprint 2 (Refazer movimentos) = 6.5h
WEEK 3: Sprint 3 (Qualidade + testes) = 7.5h

TOTAL: 23h development (~4 days senior dev)
RESULT: Production-ready ✅
```

---

## Dúvidas? 🤔

- Técnicas: Ver `PLANO_ACAO_DETALHADO.md` (tem código completo)
- Visão geral: Ver `ANALISE_PROJETO.md`
- Executivo: Ver `SUMARIO_EXECUTIVO.md`

---

**Bora começar! 🚀** Próximo passo: Dia 1, TASK 1.1
