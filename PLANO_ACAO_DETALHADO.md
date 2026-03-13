# Plano de Ação - SEFIN Audit Tool

**Objetivo**: Corrigir erros críticos e implementar melhorias de qualidade

---

## FASE 1: CORREÇÕES CRÍTICAS (1 Semana)

### 1.1 Fix Polars `.list.lengths()` Deprecation ⚠️

**Prioridade**: P0 - BLOQUEADOR  
**Tempo Estimado**: 2 horas

#### O que fazer:
1. Abrir arquivo: `cruzamentos/agrupamento_produtos.py`
2. Procurar por todas as ocorrências de `.list.lengths()`
3. Substituir por `.list.len()`
4. Testar com CNPJ real: `37671507000187`

#### Exemplo de mudança:
```python
# ❌ ANTES (Erro)
pl.col("ncms").list.lengths().alias("qtd_ncms"),

# ✅ DEPOIS (Funciona)
pl.col("ncms").list.len().alias("qtd_ncms"),
```

#### Validação:
```bash
# Testar endpoint
curl -X POST http://localhost:8001/api/python/produtos/agrupamento \
  -H "Content-Type: application/json" \
  -d '{"cnpj": "37671507000187"}'

# Esperado: HTTP 200 com resultado JSON
# Não mais: HTTP 500 com AttributeError
```

---

### 1.2 Implementar Error Handling Customizado 🛡️

**Prioridade**: P1 - IMPORTANTE  
**Tempo Estimado**: 4 horas

#### O que fazer:

##### 1. Criar `server/python/errors.py`:
```python
"""Custom error classes for SEFIN Audit API"""

class AuditError(Exception):
    """Base class for all audit errors"""
    
    def __init__(self, code: str, message: str, context: dict = None):
        self.code = code
        self.message = message
        self.context = context or {}
        self.timestamp = datetime.now().isoformat()
        super().__init__(message)
    
    def to_dict(self):
        return {
            "code": self.code,
            "message": self.message,
            "context": self.context,
            "timestamp": self.timestamp
        }


class OracleConnectionError(AuditError):
    """Raised when Oracle connection fails"""
    def __init__(self, host: str, port: int, reason: str):
        super().__init__(
            code="ORACLE_CONNECTION_ERROR",
            message=f"Failed to connect to Oracle at {host}:{port}",
            context={"host": host, "port": port, "reason": reason}
        )


class DataValidationError(AuditError):
    """Raised when data validation fails"""
    def __init__(self, field: str, value: str, expected: str):
        super().__init__(
            code="DATA_VALIDATION_ERROR",
            message=f"Invalid value for {field}",
            context={"field": field, "value": value, "expected": expected}
        )


class ParquetProcessingError(AuditError):
    """Raised when Parquet operations fail"""
    def __init__(self, operation: str, reason: str):
        super().__init__(
            code="PARQUET_PROCESSING_ERROR",
            message=f"Parquet {operation} failed",
            context={"operation": operation, "reason": reason}
        )
```

##### 2. Atualizar `server/python/api.py` - Função agrupamento:
```python
# ❌ ANTES
@app.post("/api/python/produtos/agrupamento")
async def agrupar_produtos(request: dict):
    try:
        cnpj = request.get("cnpj")
        resultado = executar_agrupamento_produtos(cnpj)
        return {"success": True, "data": resultado}
    except Exception as e:
        logger.error(f"[agrupamento_produtos] Erro: {str(e)}")
        return {"success": False, "error": str(e)}  # ❌ Sem contexto


# ✅ DEPOIS
from errors import AuditError, DataValidationError, ParquetProcessingError

@app.post("/api/python/produtos/agrupamento")
async def agrupar_produtos(request: dict):
    cnpj = request.get("cnpj", "").strip()
    
    # Validação
    if not cnpj or not cnpj.isdigit() or len(cnpj) != 14:
        raise DataValidationError("cnpj", cnpj, "14 dígitos")
    
    try:
        resultado = executar_agrupamento_produtos(cnpj)
        return {"success": True, "data": resultado}
    except AuditError as e:
        logger.warning(f"[agrupamento_produtos] {e.code}: {e.message}")
        return {"success": False, "error": e.to_dict()}, 400
    except Exception as e:
        logger.error(f"[agrupamento_produtos] Erro inesperado", exc_info=True)
        err = AuditError("INTERNAL_ERROR", str(e), {"traceback": traceback.format_exc()})
        return {"success": False, "error": err.to_dict()}, 500
```

##### 3. Remover credenciais de logs:
```python
# ❌ ANTES - NÃO FAÇA ISSO!
def conectar_oracle(user, password, host):
    logger.info(f"Conectando como {user} com senha {password} em {host}")
    # ...

# ✅ DEPOIS
def conectar_oracle(user: str, password: str, host: str):
    logger.info(f"Conectando a {host} como user=***")
    # Password e detalhes sensíveis NUNCA logados
    # Se erro, usar AuditError com contexto seguro
```

#### Validação:
```bash
# Testar com CNPJ inválido
curl -X POST http://localhost:8001/api/python/produtos/agrupamento \
  -H "Content-Type: application/json" \
  -d '{"cnpj": "invalid"}'

# Esperado: HTTP 400 com erro estruturado
# {"success": false, "error": {"code": "DATA_VALIDATION_ERROR", ...}}
```

---

### 1.3 Adicionar Validação de Entrada com Zod

**Prioridade**: P1 - IMPORTANTE  
**Tempo Estimado**: 3 horas

#### O que fazer:

##### 1. Instalar Zod:
```bash
npm install zod
```

##### 2. Criar `shared/schemas.ts`:
```typescript
import { z } from "zod";

// CNPJ sempre 14 dígitos
export const CnpjSchema = z.string()
  .regex(/^\d{14}$/, "CNPJ deve ter 14 dígitos")
  .transform(c => c.trim());

// Credenciais Oracle
export const OracleCredsSchema = z.object({
  host: z.string().min(1, "Host obrigatório"),
  port: z.number().int().min(1).max(65535),
  username: z.string().min(1, "Usuário obrigatório"),
  password: z.string().min(1, "Senha obrigatória"),
  database: z.string().optional(),
});

// Request de agrupamento
export const AgrupamentoProdutosRequestSchema = z.object({
  cnpj: CnpjSchema,
  force_recalc: z.boolean().optional().default(false),
});

// Response genérica
export const ApiResponseSchema = z.object({
  success: z.boolean(),
  data: z.any().optional(),
  error: z.any().optional(),
});
```

##### 3. Usar em routers (`server/routers.ts`):
```typescript
import { AgrupamentoProdutosRequestSchema } from "@/shared/schemas";

// Middleware de validação
const validateRequest = (schema: z.ZodSchema) => 
  async (req: any, res: any, next: any) => {
    try {
      req.validated = schema.parse(req.body);
      next();
    } catch (error) {
      if (error instanceof z.ZodError) {
        res.status(400).json({
          success: false,
          error: error.errors.map(e => ({
            field: e.path.join("."),
            message: e.message
          }))
        });
      } else {
        next(error);
      }
    }
  };

// Usar em rota
router.post(
  "/produtos/agrupamento",
  validateRequest(AgrupamentoProdutosRequestSchema),
  async (req, res) => {
    const { cnpj } = req.validated; // Type-safe!
    // ...
  }
);
```

#### Validação:
```bash
# Testar validação no frontend
npm run check  # TypeScript check

# Testar API com dados inválidos
curl -X POST http://localhost:3000/api/trpc/extracaoProdutos.agrupamento \
  -d '{"cnpj": "123"}' # Muito curto
# Esperado: 400 Bad Request com mensagens de erro
```

---

## FASE 2: FUNCIONALIDADES PENDENTES (2 Semanas)

### 2.1 Implementar "Refazer Movimentos"

**Prioridade**: P2 - BLOQUEADOR  
**Tempo Estimado**: 1 semana

Este módulo aplica o mapa de agrupamento de produtos aos dados originais e regenera as tabelas corrigidas.

#### O que fazer:

##### 1. Criar `cruzamentos/refazer_movimentos.py`:
```python
"""
Aplica mapa de agrupamento de produtos aos movimentos originais
Gera tabelas corrigidas com produtos ajustados
"""

import polars as pl
from pathlib import Path
from datetime import datetime

def refazer_nfe(cnpj_limpo: str, mapa_produto: dict, output_dir: Path) -> dict:
    """
    Recomputa tabela NFe com chave_produto ajustada
    
    Args:
        cnpj_limpo: CNPJ sem formatação (14 dígitos)
        mapa_produto: Dict com {chave_antiga: chave_nova, ...}
        output_dir: Pasta de saída
    
    Returns:
        {"success": bool, "rows_processed": int, "rows_updated": int}
    """
    nfe_path = output_dir / cnpj_limpo / "NFe_CNPJs.parquet"
    
    if not nfe_path.exists():
        raise FileNotFoundError(f"Arquivo NFe não encontrado: {nfe_path}")
    
    # Ler dados
    nfe = pl.read_parquet(nfe_path)
    rows_original = len(nfe)
    
    # Aplicar mapa
    mapa_expr = pl.col("chave_produto").map_batches(
        lambda s: s.map_dict(mapa_produto, return_dtype=pl.Utf8)
    )
    nfe_corrigida = nfe.with_columns(
        chave_produto_ajustada=mapa_expr
    )
    
    rows_updated = (nfe_corrigida["chave_produto"] != nfe_corrigida["chave_produto_ajustada"]).sum()
    
    # Salvar com versão
    timestamp = datetime.now().isoformat()
    output_file = nfe_path.parent / f"NFe_CNPJs_v{timestamp.replace(':', '-')}.parquet"
    nfe_corrigida.write_parquet(output_file)
    
    return {
        "success": True,
        "rows_processed": rows_original,
        "rows_updated": int(rows_updated),
        "output_file": str(output_file)
    }


def refazer_c170(cnpj_limpo: str, mapa_produto: dict, output_dir: Path) -> dict:
    """Recomputa tabela C170 (SPED) com código produto ajustado"""
    # Similar a refazer_nfe() mas para tabela C170
    # Agrupa por código_produto, aplica mapa, recalcula totalizações
    pass


def refazer_nfce(cnpj_limpo: str, mapa_produto: dict, output_dir: Path) -> dict:
    """Recomputa tabela NFCe com produto ajustado"""
    # Similar a refazer_nfe()
    pass


def executar_refazer_movimentos(cnpj_limpo: str, output_dir: str) -> dict:
    """
    Orquestra refazer todos os movimentos para um CNPJ
    
    Returns:
        {
            "success": bool,
            "timestamp": str,
            "resultados": {
                "nfe": {...},
                "nfce": {...},
                "c170": {...}
            }
        }
    """
    output_dir = Path(output_dir)
    
    # Ler mapa de agrupamento
    mapa_path = output_dir / cnpj_limpo / "agrupamento_mapa.json"
    if not mapa_path.exists():
        raise FileNotFoundError(f"Mapa de agrupamento não encontrado: {mapa_path}")
    
    import json
    with open(mapa_path) as f:
        mapa = json.load(f)  # {chave_antiga: chave_nova}
    
    # Executar para cada tabela
    resultados = {}
    try:
        resultados["nfe"] = refazer_nfe(cnpj_limpo, mapa, output_dir)
        resultados["nfce"] = refazer_nfce(cnpj_limpo, mapa, output_dir)
        resultados["c170"] = refazer_c170(cnpj_limpo, mapa, output_dir)
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
    
    return {
        "success": True,
        "timestamp": datetime.now().isoformat(),
        "cnpj": cnpj_limpo,
        "resultados": resultados
    }
```

##### 2. Expor em `server/python/api.py`:
```python
from cruzamentos.refazer_movimentos import executar_refazer_movimentos

@app.post("/api/python/produtos/refazer")
async def refazer_movimentos(request: dict):
    """
    POST /api/python/produtos/refazer
    
    Body: {"cnpj": "37671507000187"}
    
    Resposta:
    {
      "success": true,
      "timestamp": "2026-03-13T10:30:00",
      "resultados": {
        "nfe": {"rows_processed": 5000, "rows_updated": 250},
        "nfce": {...},
        "c170": {...}
      }
    }
    """
    cnpj = request.get("cnpj")
    
    # Validar
    if not cnpj or not cnpj.isdigit() or len(cnpj) != 14:
        raise DataValidationError("cnpj", cnpj, "14 dígitos")
    
    try:
        resultado = executar_refazer_movimentos(cnpj, output_dir)
        return resultado
    except Exception as e:
        raise AuditError("REFAZER_FAILED", str(e))
```

##### 3. Atualizar UI (`AnaliseAgrupamentoProdutos.tsx`):
```typescript
// Adicionar button após resolução em lote
<Button 
  onClick={handleRefazerMovimentos}
  disabled={!mapaCompleto}
  className="bg-blue-600"
>
  <RefreshCw className="mr-2 h-4 w-4" />
  Processar Tudo
</Button>

// Função
const handleRefazerMovimentos = async () => {
  setProcessing(true);
  try {
    const res = await fetch("/api/python/produtos/refazer", {
      method: "POST",
      body: JSON.stringify({ cnpj: cnpjAtivo })
    });
    
    const data = await res.json();
    
    if (data.success) {
      toast.success(`Processados: ${data.resultados.nfe.rows_updated} itens`);
    } else {
      toast.error(`Erro: ${data.error}`);
    }
  } finally {
    setProcessing(false);
  }
};
```

#### Validação:
```bash
# 1. Criar agrupamento
curl -X POST http://localhost:8001/api/python/produtos/agrupamento \
  -d '{"cnpj": "37671507000187"}'

# 2. Refazer movimentos
curl -X POST http://localhost:8001/api/python/produtos/refazer \
  -d '{"cnpj": "37671507000187"}'

# 3. Validar: totais antes = totais depois
# (somar items origem e comparar com itens destino)
```

---

## FASE 3: QUALIDADE E TESTES (1-2 Semanas)

### 3.1 Adicionar Testes Unitários

**Prioridade**: P2  
**Tempo Estimado**: 1 semana

#### Criar `server/test/validators.test.ts`:
```typescript
import { describe, it, expect } from "vitest";
import { CnpjSchema, OracleCredsSchema } from "@/shared/schemas";
import { z } from "zod";

describe("Input Validators", () => {
  describe("CnpjSchema", () => {
    it("should validate correct CNPJ", () => {
      expect(() => CnpjSchema.parse("37671507000187")).not.toThrow();
    });
    
    it("should reject CNPJ with less than 14 digits", () => {
      expect(() => CnpjSchema.parse("3767150700018")).toThrow(z.ZodError);
    });
    
    it("should reject non-numeric CNPJ", () => {
      expect(() => CnpjSchema.parse("3767150700018A")).toThrow(z.ZodError);
    });
  });
  
  describe("OracleCredsSchema", () => {
    it("should validate correct credentials", () => {
      const valid = {
        host: "192.168.1.1",
        port: 1521,
        username: "sefin",
        password: "safe_password"
      };
      expect(() => OracleCredsSchema.parse(valid)).not.toThrow();
    });
    
    it("should reject invalid port", () => {
      const invalid = {
        host: "192.168.1.1",
        port: 99999,
        username: "sefin",
        password: "password"
      };
      expect(() => OracleCredsSchema.parse(invalid)).toThrow(z.ZodError);
    });
  });
});
```

#### Criar `cruzamentos/test_agrupamento.py`:
```python
import pytest
from pathlib import Path
from cruzamentos.agrupamento_produtos import executar_agrupamento_produtos

CNPJ_TEST = "37671507000187"
OUTPUT_DIR = Path("./test_output")

def test_agrupamento_produtos():
    """Test grouping with real CNPJ (requires Oracle access)"""
    resultado = executar_agrupamento_produtos(CNPJ_TEST)
    
    assert resultado["success"] == True
    assert "discrepancias" in resultado["data"]
    assert "duplicidades" in resultado["data"]
    assert len(resultado["data"]["discrepancias"]) > 0


def test_agrupamento_com_cnpj_invalido():
    """Should reject invalid CNPJ"""
    with pytest.raises(ValueError):
        executar_agrupamento_produtos("invalid_cnpj")


def test_refazer_movimentos():
    """Test movement recreation"""
    from cruzamentos.refazer_movimentos import executar_refazer_movimentos
    
    resultado = executar_refazer_movimentos(CNPJ_TEST, str(OUTPUT_DIR))
    
    assert resultado["success"] == True
    assert resultado["resultados"]["nfe"]["rows_processed"] > 0
```

#### Rodar testes:
```bash
# Unit tests
npm run test

# Python tests
pytest cruzamentos/test_agrupamento.py -v
```

---

## Timeline Recomendada

| Semana | Tarefa | Horas | Status |
|--------|--------|-------|--------|
| 1 | Fix Polars API | 8 | ⏳ TODO |
| 1 | Error handling + Zod | 8 | ⏳ TODO |
| 2 | Refazer movimentos impl | 16 | ⏳ TODO |
| 2 | Testes unitários | 12 | ⏳ TODO |
| 3 | Code review + ajustes | 8 | ⏳ TODO |
| **Total** | | **52 horas** | |

---

## Critérios de Aceição

- [x] Agrupamento produtos retorna HTTP 200 (sem erro Polars)
- [x] Credenciais não aparecem em logs
- [x] Validação Zod em routers críticos
- [x] Error responses estruturados com código + contexto
- [x] Refazer movimentos cria arquivos versionados
- [x] Testes cobrem 70% do código crítico
- [x] Sem warnings TypeScript (`npm run check`)

---

**Próximo passo**: Iniciar Fase 1 - Correções Críticas
