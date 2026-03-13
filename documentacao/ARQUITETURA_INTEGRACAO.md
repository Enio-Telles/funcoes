# Arquitetura e Integração Python-Node-React 🏗️

Este documento explica em detalhes como o Python é integrado ao SEFIN Audit Tool e como a comunicação entre as três camadas (React, Node.js, Python) funciona.

---

## 📊 Visão Geral da Arquitetura

### Três Camadas Distintas

```
┌─────────────────────────────────────────────────────────────────┐
│ CAMADA 1: FRONTEND (REACT)                                      │
│ - Componentes UI (Tabelas, Gráficos, Formulários)              │
│ - Chamadas para tRPC (/api/trpc)                               │
│ - Sem acesso direto ao Oracle ou Python                        │
└─────────────────────────────────────────────────────────────────┘
                              │ tRPC
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ CAMADA 2: ORQUESTRAÇÃO (NODE.JS + EXPRESS + tRPC)              │
│ - Validação de Autenticação (JWT/OAuth)                        │
│ - Roteamento e Orquestração (routers.ts)                       │
│ - Proxy inteligente para Python (/api/python/*)                │
│ - Gerenciamento de metadados (Drizzle ORM)                     │
└─────────────────────────────────────────────────────────────────┘
                         │ HTTP/JSON
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ CAMADA 3: PROCESSAMENTO (PYTHON + FASTAPI)                      │
│ - Conexão Oracle (oracledb driver)                              │
│ - Processamento com Polars (high-performance)                   │
│ - Análises e Cruzamentos                                        │
│ - Leitura/Escrita Parquet                                       │
│ - Geração de Relatórios (docx, xlsx)                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔌 Como React Chama Python

### Exemplo: Extração de Dados

#### 1️⃣ React chama tRPC

```tsx
// client/src/pages/Extracao.tsx
const { mutate: extrairDados } = api.extraction.extract.useMutation();

extrairDados({
  cnpj: "12345678000190",
  outputDir: "C:\\dados\\extraido",
  queries: ["consultas_fonte/C100.sql", "consultas_fonte/C170.sql"]
});
```

#### 2️⃣ tRPC chama Node.js Router

```typescript
// server/routers.ts
export const appRouter = router({
  extraction: router({
    extract: protectedProcedure
      .input(ExtractionSchema)
      .mutation(async ({ input }) => {
        // Valida autenticação implicitamente (protectedProcedure)
        // Faz a chamada para Python via proxy
        const response = await fetch('http://localhost:8001/api/python/oracle/extract', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(input)
        });
        return await response.json();
      })
  })
});
```

#### 3️⃣ Node.js Faz Proxy para Python

```typescript
// server/_core/index.ts
app.all("/api/python/*", async (req, res) => {
  try {
    const targetUrl = `http://localhost:8001${req.originalUrl}`;
    const response = await fetch(targetUrl, {
      method: req.method,
      headers: req.headers,
      body: req.body ? JSON.stringify(req.body) : undefined
    });
    
    // Espelha status, headers e conteúdo
    res.status(response.status);
    res.send(await response.json());
  } catch (error) {
    res.status(502).json({ detail: "Python API unavailable" });
  }
});
```

#### 4️⃣ Python FastAPI Processa

```python
# server/python/api.py
@app.post("/api/python/oracle/extract")
async def extract(request: ExtractionRequest):
    """Executa SQL e salva em Parquet."""
    import oracledb
    
    # Conexão Oracle
    conexao = oracledb.connect(**request.connection.dict())
    
    # Para cada query
    for query_path in request.queries:
        sql = ler_sql(Path(query_path))
        params = extrair_parametros_sql(sql)
        
        # Executa
        with conexao.cursor() as cursor:
            cursor.execute(sql, {"cnpj": request.cnpj})
            rows = cursor.fetchall()
        
        # Converte para DataFrame Polars
        df = pl.DataFrame(...)
        
        # Salva Parquet
        df.write_parquet(f"{request.output_dir}/{nome}.parquet")
    
    return {"success": True, "files_created": [...]}
```

#### 5️⃣ React Recebe Resultado

```tsx
// A callback do mutate recebe a resposta
extrairDados(
  { ... },
  {
    onSuccess: (data) => {
      console.log(`✓ ${data.files_created.length} arquivos criados!`);
      // Atualiza UI ou navega para próxima tela
    }
  }
);
```

---

## 🧵 Sequência Completa: Fluxo de uma Requisição

```sequence
React Browser              Node.js Server            Python API
    │                          │                          │
    │ ① tRPC POST              │                          │
    ├─/api/trpc────────────────>                         │
    │                          │                          │
    │                    ② Valida JWT                     │
    │                          │                          │
    │                    ③ Faz HTTP proxy                 │
    │                          ├──────────────────────────>
    │                          │                          │
    │                          │              ④ Conecta Oracle
    │                          │                 Executa SQL
    │                          │                 Processa Polars
    │                          │                 Salva Parquet
    │                          │<──────────────────────────
    │                    ⑤ Retorna JSON                   │
    │<────────────────────────── │                        │
    │                          │                          │
    ⑥ Atualiza UI              │                          │
    com resultado              │                          │
```

---

## 🔗 Dois Servidores Rodando em Paralelo

### Port Mapping

| Aplicação | Porta | URL | Descrição |
|-----------|-------|-----|-----------|
| **React** (Frontend) | 3000 | http://localhost:3000 | Vite dev server |
| **Node.js** (Orquestração) | 3000 | http://localhost:3000 | Express (mesma porta Vite) |
| **Python** (Dados) | 8001 | http://localhost:8001 | FastAPI |

### Como Iniciar

```bash
# Terminal 1: Frontend + Node.js (mesma porta com Vite proxy)
pnpm dev
# Inicia Vite em 3000, redireciona /api/* para Express

# Terminal 2: Python (porta separada)
cd server/python
python -m uvicorn api:app --port 8001 --reload
```

### Por Que Três Portas?

- **Vite (3000)** servindo Frontend em desenvolvimento
- **Express (3000)** rodando tRPC para requisições /api/*
- **FastAPI (8001)** rodando operações pesadas do Python isoladas

---

## 📁 Organização de Código Relevante

### Arquivos Node.js (Orquestração)

```typescript
server/
├── routers.ts              # RESTful do tRPC (exemplo: extraction.extract)
├── index.ts                # Express + setup de middleware
├── _core/
│   ├── index.ts           # Proxy para Python
│   ├── context.ts         # Contexto tRPC (usuário, req/res)
│   ├── trpc.ts            # Setup tRPC base
│   └── env.ts             # Variáveis de ambiente
└── python/
    └── ... (vazio, Python é externo)
```

### Arquivos Python (Processamento)

```python
server/python/
├── api.py                  # 📌 ARQUIVO PRINCIPAL - Todos endpoints
├── gerar_relatorio.py      # Helper para gerar Word/Excel
├── start.sh                # Script para iniciar servidor
└── __pycache__/

# Imports para análises
import sys
sys.path.insert(0, "cruzamentos")
from ressarcimento import ...
from omissao_saida import ...
```

### Estudar: Imports Críticos em api.py

```python
# Linhas 30-40 de server/python/api.py
_PROJETO_DIR = Path(__file__).resolve().parent.parent.parent
_CRUZAMENTOS_DIR = _PROJETO_DIR / "cruzamentos"

# Adiciona cruzamentos ao path para importações
sys.path.insert(0, str(_CRUZAMENTOS_DIR))

# Agora pode fazer:
from ressarcimento.analise_ressarcimento import executar_analise
from omissao_saida.analise_omissao import executar_analise_omissao
```

---

## 🔐 Autenticação e Segurança

### Fluxo de Autenticação

```
1. Usuário faz login (OAuth ou credencial local)
2. Node.js gera JWT/Cookie seguro
3. React armazena token do cliente
4. Requisição tRPC inclui token automaticamente
5. Node.js valida JWT antes de processar
6. Se válido, proxy para Python (credenciais não vazam)
7. Python executa sem conhecer detalhes de autenticação
```

### Proteção de Endpoints tRPC

```typescript
// Verifica autenticação ANTES de chamar Python
const protectedProcedure = t.procedure.use(
  t.middleware(async (opts) => {
    if (!opts.ctx.user) {
      throw new TRPCError({ code: "UNAUTHORIZED" });
    }
    return opts.next();
  })
);

// Uso
export const extraction = protectedProcedure
  .input(ExtractionSchema)
  .mutation(async ({ input, ctx }) => {
    // ctx.user garante autenticação
    // input é validado por Zod
    // Só depois chama Python
  })
```

---

## 🌍 Comunicação via HTTP/JSON

### Exemplo: Request de Parquet Read

**React → Node.js:**
```json
POST /api/trpc
{
  "0": {
    "jsonrpc": "2.0",
    "id": "1",
    "method": "query",
    "params": {
      "path": "parquet.readParquet",
      "input": {
        "file_path": "C:\\dados\\nfe.parquet",
        "page": 1,
        "page_size": 50,
        "filters": { "icms": "ST" }
      }
    }
  }
}
```

**Node.js → Python:**
```json
POST /api/python/parquet/read
{
  "file_path": "C:\\dados\\nfe.parquet",
  "page": 1,
  "page_size": 50,
  "filters": { "icms": "ST" }
}
```

**Python Response:**
```json
{
  "columns": ["id", "icms", "valor", ...],
  "rows": [...],
  "total_rows": 15000,
  "filtered_rows": 342,
  "page": 1,
  "total_pages": 7
}
```

---

## ⚠️ Tratamento de Erros

### Erro no Python

```python
@app.post("/api/python/oracle/extract")
async def extract(request: ExtractionRequest):
    try:
        # ... executa SQL
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        # FastAPI converte para JSON automático
```

### Erro no Node.js (Proxy)

```typescript
app.all("/api/python/*", async (req, res) => {
  try {
    // ... chamada para Python
  } catch (error: any) {
    res.status(502).json({
      detail: `Python API unavailable: ${error?.message}`
    });
  }
});
```

### Erro no React

```tsx
const { mutate, error } = api.extraction.extract.useMutation();

if (error) {
  // error.message contém détail do Python ou Node.js
  console.error("❌ Erro:", error.message);
}
```

---

## 🔄 Exemplo Real: Análise de Ressarcimento

### Fluxo Completo

```
1. React: Usuário clica em "Analisar Ressarcimento"
   └─> Envia CNPJ e período

2. Node.js: Recebe requisição tRPC
   └─> Valida usuário
   └─> Faz proxy para /api/python/analytics/ressarcimento

3. Python:
   ├─> Carrega dados: C176, NFe, C170, Fronteira (Parquet+Oracle)
   ├─> Importa módulo: from ressarcimento.analise_ressarcimento import *
   ├─> Executa cruzamentos (carregar → cruzar → selecionar colunas)
   ├─> Calcula v_ress_st_1, v_ress_st_2
   └─> Retorna DataFrame com resultados

4. React: Exibe tabela interativa com resultados
   └─> Usuário pode exportar para Excel/Word
```

---

## 📝 Checklist de Integração Python

- ✅ Python API rodando em porta 8001
- ✅ Node.js consegue alcançar `http://localhost:8001/api/python/*`
- ✅ Endpoints tRPC estão mapeados e tipados
- ✅ Credenciais Oracle não são expostas ao cliente
- ✅ Tratamento de erro em cascata (Python → Node.js → React)
- ✅ Parquets salvos em local acessível
- ✅ Módulos Python (cruzamentos) importados via sys.path.insert()

---

**Ver também:**
- [ANALISES_MODULOS.md](./ANALISES_MODULOS.md) - Detalhes de cada análise
- [ENDPOINTS_PYTHON.md](./ENDPOINTS_PYTHON.md) - Referência de endpoints
- [GUIA_DESENVOLVIMENTO.md](./GUIA_DESENVOLVIMENTO.md) - Como adicionar análises
