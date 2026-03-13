# Referência de Endpoints Python - FastAPI 📡

Documentação completa de todos os endpoints disponíveis na API FastAPI (`server/python/api.py`).

---

## 📚 Índice de Endpoints

| Categoria | Endpoint | Método | Descrição |
|-----------|----------|--------|-----------|
| **Health** | [/api/python/health](#health-check) | GET | Status da API |
| **CNPJ** | [/api/python/validate-cnpj](#validacao-cnpj) | GET | Valida CNPJ |
| **Oracle** | [/api/python/oracle/test-connection](#teste-conexao-oracle) | POST | Testa conexão |
| **Oracle** | [/api/python/oracle/extract](#extracao-oracle) | POST | Extrai dados |
| **Oracle** | [/api/python/oracle/credentials](#get-credenciais) | GET | Recupera credenciais |
| **Oracle** | [/api/python/oracle/save-credentials](#salva-credenciais) | POST | Salva credenciais |
| **Oracle** | [/api/python/oracle/clear-credentials](#limpa-credenciais) | DELETE | Remove credenciais |
| **Parquet** | [/api/python/parquet/read](#leitura-parquet) | POST | Lê arquivo |
| **Parquet** | [/api/python/parquet/write-cell](#escrita-parquet) | POST | Edita célula |
| **Parquet** | [/api/python/parquet/add-row](#adiciona-linha) | POST | Nova linha |
| **Parquet** | [/api/python/parquet/add-column](#adiciona-coluna) | POST | Nova coluna |
| **Parquet** | [/api/python/parquet/list](#lista-arquivos) | GET | Lista Parquets |
| **Parquet** | [/api/python/parquet/unique-values](#valores-unicos) | GET | Valores únicos |
| **FS** | [/api/python/filesystem/browse](#navegacao-fs) | GET | Navega discos |
| **FS** | [/api/python/filesystem/sql-queries](#lista-sql) | GET | Lista .sql |
| **Relatórios** | [/api/python/reports/timbrado](#relatorio-word) | POST | Gera Word |
| **Relatórios** | [/api/python/reports/det-notification](#relatorio-det) | POST | Gera DET |
| **Exportação** | [/api/python/export/excel](#export-excel) | POST | Exporta Excel |
| **Exportação** | [/api/python/export/excel-download](#download-excel) | GET | Download Excel |
| **Produtos** | [/api/python/produtos/revisao-manual](#produtos-revisao-manual) | GET | Lista pendências |
| **Produtos** | [/api/python/produtos/detalhes-codigo](#produtos-detalhes-codigo) | GET | Detalhes por código |
| **Produtos** | [/api/python/produtos/detalhes-multi-codigo](#produtos-detalhes-multi-codigo) | POST | Detalhes multi |
| **Produtos** | [/api/python/produtos/revisao-manual/submit](#produtos-revisao-manual-submit) | POST | Submete decisões |
| **Produtos** | [/api/python/produtos/resolver-manual-unificar](#produtos-resolver-manual-unificar) | POST | Unificar |
| **Produtos** | [/api/python/produtos/resolver-manual-desagregar](#produtos-resolver-manual-desagregar) | POST | Desagregar |
| **Referências** | [/api/python/referencias/ncm/{codigo}](#referencias-ncm) | GET | Consulta NCM |
| **Referências** | [/api/python/referencias/cest/{codigo}](#referencias-cest) | GET | Consulta CEST |

---

## 🔍 Health & System

### Health Check

**Endpoint:** `GET /api/python/health`

**Descrição:** Verifica se API está rodando e retorna status

**Response:**
```json
{
  "status": "ok",
  "engine": "polars",
  "version": "1.0.0"
}
```

**Uso:**
```bash
curl http://localhost:8001/api/python/health
```

---

## ✔️ Validação

### Validação CNPJ

**Endpoint:** `GET /api/python/validate-cnpj`

**Query Parameters:**
| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `cnpj` | string | Sim | CNPJ com ou sem máscara |

**Response:**
```json
{
  "valid": true,
  "cnpj_limpo": "12345678000190",
  "cnpj_formatado": "12.345.678/0001-90"
}
```

**Exemplos:**
```bash
# Com máscara
curl "http://localhost:8001/api/python/validate-cnpj?cnpj=12.345.678%2F0001-90"

# Sem máscara
curl "http://localhost:8001/api/python/validate-cnpj?cnpj=12345678000190"

# Inválido
curl "http://localhost:8001/api/python/validate-cnpj?cnpj=00000000000000"
# Response: {"valid": false}
```

---

## 🔐 Oracle - Credenciais

### Teste de Conexão Oracle

**Endpoint:** `POST /api/python/oracle/test-connection`

**Headers:**
```
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "host": "exa01-scan.sefin.ro.gov.br",
  "port": 1521,
  "service": "sefindw",
  "user": "seu_usuario",
  "password": "sua_senha"
}
```

**Response (Sucesso):**
```json
{
  "success": true,
  "message": "Conexão estabelecida com sucesso",
  "database_info": "Oracle Database 19c Enterprise Edition..."
}
```

**Response (Erro):**
```json
{
  "success": false,
  "error": "ORA-12514: TNS:listener could not resolve SERVICE_NAME in connect descriptor"
}
```

**Exemplo cURL:**
```bash
curl -X POST http://localhost:8001/api/python/oracle/test-connection \
  -H "Content-Type: application/json" \
  -d '{
    "host": "exa01-scan.sefin.ro.gov.br",
    "port": 1521,
    "service": "sefindw",
    "user": "seu_usuario",
    "password": "sua_senha"
  }'
```

### Get Credenciais Salvas

**Endpoint:** `GET /api/python/oracle/credentials`

**Response (Com credenciais):**
```json
{
  "success": true,
  "has_credentials": true,
  "user": "seu_usuario",
  "password": "sua_senha"
}
```

**Response (Sem credenciais):**
```json
{
  "success": true,
  "has_credentials": false
}
```

### Salvar Credenciais

**Endpoint:** `POST /api/python/oracle/save-credentials`

**Body:**
```json
{
  "host": "exa01-scan.sefin.ro.gov.br",
  "port": 1521,
  "service": "sefindw",
  "user": "seu_usuario",
  "password": "sua_senha"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Credenciais salvas com sucesso no Cofre do Windows"
}
```

**⚠️ Nota:** Senha é armazenada no Windows Credential Manager (seguro)

### Limpar Credenciais

**Endpoint:** `DELETE /api/python/oracle/clear-credentials`

**Response:**
```json
{
  "success": true,
  "message": "Credenciais removidas com sucesso"
}
```

---

## 📥 Oracle - Extração

### Extração Completa

**Endpoint:** `POST /api/python/oracle/extract`

**Headers:**
```
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "connection": {
    "host": "exa01-scan.sefin.ro.gov.br",
    "port": 1521,
    "service": "sefindw",
    "user": "seu_usuario",
    "password": "sua_senha"
  },
  "cnpj": "12345678000190",
  "output_dir": "C:\\dados\\37671507000187",
  "queries": [
    "consultas_fonte/C100.sql",
    "consultas_fonte/C170.sql",
    "consultas_fonte/C176.sql"
  ],
  "include_auxiliary": true,
  "auxiliary_queries_dir": "consultas_fonte/auxiliares",
  "normalize_columns": true,
  "parameters": {
    "data_inicio": "2024-01-01",
    "data_fim": "2024-12-31"
  }
}
```

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "query": "C100",
      "rows": 1250,
      "columns": 42,
      "file": "C:\\dados\\37671507000187\\c100_12345678000190.parquet",
      "status": "success"
    },
    {
      "query": "C170",
      "rows": 8932,
      "columns": 58,
      "file": "C:\\dados\\37671507000187\\c170_12345678000190.parquet",
      "status": "success"
    },
    {
      "query": "[AUX] auxiliar_1",
      "rows": 340,
      "columns": 12,
      "file": "C:\\dados\\37671507000187\\tabelas_auxiliares\\auxiliar_1.parquet",
      "status": "success"
    }
  ],
  "output_dir": "C:\\dados\\37671507000187"
}
```

**Exemplo cURL:**
```bash
curl -X POST http://localhost:8001/api/python/oracle/extract \
  -H "Content-Type: application/json" \
  -d @- << 'EOF'
{
  "connection": {
    "host": "exa01-scan.sefin.ro.gov.br",
    "port": 1521,
    "service": "sefindw",
    "user": "seu_usuario",
    "password": "sua_senha"
  },
  "cnpj": "12345678000190",
  "output_dir": "C:\\dados",
  "queries": ["consultas_fonte/C100.sql"]
}
EOF
```

---

## 📊 Parquet - Leitura e Escrita

### Leitura Parquet (com Paginação)

**Endpoint:** `POST /api/python/parquet/read`

**Body:**
```json
{
  "file_path": "C:\\dados\\37671507000187\\c100_12345678000190.parquet",
  "page": 1,
  "page_size": 50,
  "filters": {
    "tipo_documento": "00",
    "cfop": "5102"
  },
  "sort_column": "data_emissao",
  "sort_direction": "desc"
}
```

**Response:**
```json
{
  "columns": ["id", "chave_nfe", "data_emissao", "valor", "icms", "tipo_documento"],
  "dtypes": {
    "id": "Int32",
    "chave_nfe": "String",
    "data_emissao": "Date",
    "valor": "Float64",
    "icms": "Float64"
  },
  "rows": [
    {
      "id": 1,
      "chave_nfe": "35240901234567000190550010000000011234567890",
      "data_emissao": "2024-09-15",
      "valor": 1234.50,
      "icms": 222.21,
      "tipo_documento": "00"
    }
  ],
  "total_rows": 1250,
  "filtered_rows": 42,
  "page": 1,
  "page_size": 50,
  "total_pages": 1,
  "file_name": "c100_12345678000190.parquet"
}
```

### Escrita (Edit Célula)

**Endpoint:** `POST /api/python/parquet/write-cell`

**Body:**
```json
{
  "file_path": "C:\\dados\\resultado.parquet",
  "row_index": 5,
  "column": "status",
  "value": "CORRIGIDO"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Célula atualizada"
}
```

### Adiciona Linha

**Endpoint:** `POST /api/python/parquet/add-row`

**Body:**
```json
{
  "file_path": "C:\\dados\\resultado.parquet"
}
```

**Response:**
```json
{
  "success": true,
  "new_row_count": 1251
}
```

### Adiciona Coluna

**Endpoint:** `POST /api/python/parquet/add-column`

**Body:**
```json
{
  "file_path": "C:\\dados\\resultado.parquet",
  "column_name": "status_auditoria",
  "default_value": "PENDENTE"
}
```

**Response:**
```json
{
  "success": true,
  "column_name": "status_auditoria",
  "total_columns": 43
}
```

### Lista Arquivos Parquet

**Endpoint:** `GET /api/python/parquet/list`

**Query Parameters:**
| Parâmetro | Type | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `directory` | string | Sim | Caminho da pasta |

**Response:**
```json
{
  "directory": "C:\\dados\\37671507000187",
  "files": [
    {
      "name": "c100_12345678000190.parquet",
      "path": "C:\\dados\\37671507000187\\c100_12345678000190.parquet",
      "size": 2048576,
      "size_human": "2.0 MB",
      "rows": 1250,
      "columns": 42,
      "modified": "2024-03-05T14:30:00",
      "relative_path": "c100_12345678000190.parquet"
    }
  ],
  "count": 3
}
```

### Valores Únicos (Coluna)

**Endpoint:** `GET /api/python/parquet/unique-values`

**Query Parameters:**
| Parâmetro | Type | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `file_path` | string | Sim | Caminho Parquet |
| `column` | string | Sim | Nome da coluna |

**Response:**
```json
{
  "column": "cfop",
  "values": ["5102", "5103", "5104", "5201", "6102"]
}
```

---

## 📁 Sistema de Arquivos

### Navegação de Discos/Pastas

**Endpoint:** `GET /api/python/filesystem/browse`

**Query Parameters:**
| Parâmetro | Type | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `path` | string | Não | Caminho atual (branco = home) |

**Response (Windows - Raiz):**
```json
{
  "current": "",
  "parent": null,
  "entries": [
    {"name": "C:\\", "path": "C:\\", "has_children": true},
    {"name": "D:\\", "path": "D:\\", "has_children": true}
  ]
}
```

**Response (Dentro de pasta):**
```json
{
  "current": "C:\\Users\\eniot\\Documents",
  "parent": "C:\\Users\\eniot",
  "entries": [
    {"name": "sefin_audit", "path": "C:\\Users\\eniot\\Documents\\sefin_audit", "has_children": true},
    {"name": "dados", "path": "C:\\Users\\eniot\\Documents\\dados", "has_children": true}
  ]
}
```

### Lista Queries SQL

**Endpoint:** `GET /api/python/filesystem/sql-queries`

**Query Parameters:**
| Parâmetro | Type | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `path` | string | Sim | Caminho pasta ou arquivo .sql |

**Response:**
```json
{
  "queries": [
    {
      "name": "C100.sql",
      "path": "C:\\projeto\\consultas_fonte\\C100.sql",
      "parameters": ["cnpj", "cnpj_raiz"],
      "size": 2048
    },
    {
      "name": "C170.sql",
      "path": "C:\\projeto\\consultas_fonte\\C170.sql",
      "parameters": ["cnpj"],
      "size": 3456
    }
  ]
}
```

---

## 📄 Relatórios

### Gerar Relatório Word (Timbrado)

**Endpoint:** `POST /api/python/reports/timbrado`

**Body:**
```json
{
  "orgao": "GERÊNCIA DE FISCALIZAÇÃO",
  "razao_social": "Empresa Teste LTDA",
  "cnpj": "12345678000190",
  "ie": "111.111.111.111",
  "situacao_ie": "Ativa",
  "regime_pagamento": "Mensal",
  "regime_especial": "SIMPLES",
  "atividade_principal": "Comércio de produtos",
  "endereco": "Rua Teste, 123",
  "num_dsf": "DSF-2024-001",
  "objeto": "Auditoria Fiscal",
  "relato": "Durante a auditoria verificamos...",
  "itens": [
    {
      "item": 1,
      "descricao": "Omissão de ICMS em C100",
      "valor": 10000.00,
      "aliquota": 18.0
    }
  ],
  "conclusao": "Recomenda-se ...",
  "afte": "João Silva",
  "matricula": "12345",
  "data_extenso": "cinco de março de dois mil e vinte e quatro"
}
```

**Response:**
```json
{
  "success": true,
  "file": "C:\\temp\\relatorio_timbrado_12345678000190.docx",
  "size": 102400
}
```

### Gerar Notificação DET

**Endpoint:** `POST /api/python/reports/det-notification`

**Body:**
```json
{
  "razao_social": "Empresa Teste LTDA",
  "cnpj": "12345678000190",
  "ie": "111.111.111.111",
  "endereco": "Rua Teste, 123",
  "dsf": "DSF-2024-001",
  "assunto": "Notificação de Irregularidade Fiscal",
  "corpo": "Conforme verificação em nossos registros...",
  "afte": "João Silva",
  "matricula": "12345"
}
```

**Response:**
```json
{
  "success": true,
  "file": "C:\\temp\\notificacao_det_12345678000190.txt",
  "content": "GOVERNO DO ESTADO DE RONDÔNIA..."
}
```

---

## 💾 Exportação

## 🧩 Produtos

### Produtos — Revisão Manual
**Endpoint:** `GET /api/python/produtos/revisao-manual`

Query:
- `cnpj` (string, obrigatório)

Resposta: lista de produtos com `requer_revisao_manual` e metadados.

### Produtos — Detalhes por Código
**Endpoint:** `GET /api/python/produtos/detalhes-codigo`

Query:
- `cnpj` (string), `codigo` (string)

Resposta: linhas fonte associadas ao código master.

### Produtos — Detalhes Multi-Código
**Endpoint:** `POST /api/python/produtos/detalhes-multi-codigo`

Body (JSON):
```json
{ "cnpj": "37671507000187", "codigos": ["P001", "P002"] }
```

### Produtos — Submeter Revisão Manual
**Endpoint:** `POST /api/python/produtos/revisao-manual/submit`

Body (JSON):
```json
{ "cnpj": "37671507000187", "decisoes": [ { "acao": "unificar", "codigo": "P001", "ncm": "12345678" } ] }
```

### Produtos — Resolver Manual (Unificar)
**Endpoint:** `POST /api/python/produtos/resolver-manual-unificar`

### Produtos — Resolver Manual (Desagregar)
**Endpoint:** `POST /api/python/produtos/resolver-manual-desagregar`

## 📚 Referências

### Referências — NCM
**Endpoint:** `GET /api/python/referencias/ncm/{codigo}`

### Referências — CEST
**Endpoint:** `GET /api/python/referencias/cest/{codigo}`

### Exportar Parquet para Excel

**Endpoint:** `POST /api/python/export/excel`

**Body:**
```json
{
  "source_files": [
    "C:\\dados\\c100_12345678000190.parquet",
    "C:\\dados\\c170_12345678000190.parquet"
  ],
  "output_dir": "C:\\relatorios"
}
```

**Response:**
```json
{
  "success": true,
  "files_created": [
    {
      "source": "c100_12345678000190.parquet",
      "output": "C:\\relatorios\\c100_12345678000190.xlsx",
      "rows": 1250,
      "columns": 42,
      "size": 524288
    }
  ]
}
```

### Download Excel (Streaming)

**Endpoint:** `GET /api/python/export/excel-download`

**Query Parameters:**
| Parâmetro | Type | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `file_path` | string | Sim | Caminho Parquet |

**Response:** Arquivo Excel em stream (use para download)

**Exemplo:**
```bash
curl -O "http://localhost:8001/api/python/export/excel-download?file_path=C%3A%5Cdados%5Cc100.parquet"
# Salva como c100.xlsx
```

---

## 📊 Análises (Analytics)

### Análise de Ressarcimento ICMS ST

**Endpoint:** `POST /api/python/analytics/ressarcimento`

**Body:**
```json
{
  "cnpj": "12345678000190",
  "data_ini": "2024-01-01",
  "data_fim": "2024-12-31",
  "input_dir": "C:\\dados\\37671507000187",
  "output_dir": "C:\\relatorios"
}
```

**Response:**
```json
{
  "success": true,
  "cnpj": "12345678000190",
  "periodo": "2024-01-01 to 2024-12-31",
  "arquivo_saida": "C:\\relatorios\\analise_ressarcimento_12345678000190.parquet",
  "registros_processados": 1250,
  "registros_resultado": 1180,
  "resumo": {
    "total": 1180,
    "alertas": 45,
    "conformidade": 96.2
  }
}
```

### Análise de Omissão de Saída

**Endpoint:** `POST /api/python/analytics/omissao_saida`

**Body:**
```json
{
  "cnpj": "12345678000190",
  "data_ini": "2024-01-01",
  "data_fim": "2024-03-31",
  "input_dir": "C:\\dados",
  "output_dir": "C:\\relatorios",
  "tolerancia_dias": 45,
  "tolerancia_percentual": 5.0
}
```

**Response:**
```json
{
  "success": true,
  "cnpj": "12345678000190",
  "periodo": "2024-01",
  "total_entradas": 1250,
  "entradas_com_saida": 1180,
  "entradas_omissao_parcial": 35,
  "entradas_omissao_total": 35,
  "valor_omitido_icms": 45670.50,
  "taxa_conformidade": 94.4,
  "arquivo_saida": "C:\\relatorios\\analise_omissao_12345678000190.parquet"
}
```

---

## ⚠️ Tratamento de Erros

Todos os endpoints retornam padrão de erro:

```json
{
  "detail": "Mensagem de erro descritiva"
}
```

### Códigos HTTP

| Code | Significado |
|------|-----------|
| 200 | ✅ Sucesso |
| 400 | ❌ Parâmetro inválido ou faltando |
| 404 | ❌ Arquivo/recurso não encontrado |
| 500 | ❌ Erro interno do servidor |
| 502 | ❌ Python API indisponível (via proxy Node.js) |

---

## 🔗 Documentação Interativa

Acesse **Swagger UI** para explorar todos os endpoints:

```
http://localhost:8001/docs
```

Ou **ReDoc** (view alternativa):

```
http://localhost:8001/redoc
```

---

**Ver também:**
- [ARQUITETURA_INTEGRACAO.md](./ARQUITETURA_INTEGRACAO.md) - Como os endpoints são integrados
- [ANALISES_MODULOS.md](./ANALISES_MODULOS.md) - Detalhes das análises
- [SETUP_AMBIENTE.md](./SETUP_AMBIENTE.md) - Como configurar a API Python
