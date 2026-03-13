# Estrutura do Projeto - Mapa Completo 🗺️

Documentação detalhada da organização de arquivos e pastas do SEFIN Audit Tool.

---

## 📦 Estrutura Hierárquica Completa

```
sefin-audit-tool/
│
├── 📄 Arquivos de Configuração
│   ├── .env                          # Variáveis de ambiente (NÃO commitar)
│   ├── .env.example                  # Template de .env
│   ├── .gitignore                    # Arquivos ignorados pelo Git
│   ├── package.json                  # Dependências Node.js
│   ├── pnpm-lock.yaml                # Lock file do pnpm
│   ├── tsconfig.json                 # Config TypeScript
│   ├── tsconfig.node.json            # Config TypeScript (build)
│   ├── vite.config.ts                # Config Vite (frontend)
│   ├── vitest.config.ts              # Config testes (vitest)
│   ├── drizzle.config.ts             # Config Drizzle ORM
│   └── components.json               # Config de componentes
│
├── 📄 Documentação Raiz
│   ├── README.md                     # Documentação principal
│   ├── QUICKSTART.md                 # Guia de instalação rápida
│   ├── ARCHITECTURE.md               # Visão geral da arquitetura
│   ├── CONTRIBUTING.md               # Guia de contribuição
│   ├── implementation_plan.md.resolved
│   ├── todo.md                       # Tasks pendentes
│   ├── ideas.md                      # Ideias futuras
│   ├── plano_melhora.md             # Plano de melhorias
│   └── screenshot_notes.md           # Anotações sobre screenshots
│
├── 📁 documentacao/                  # 👈 DOCUMENTAÇÃO CONSOLIDADA (novo!)
│   ├── README.md                     # Índice de documentação
│   ├── ARQUITETURA_INTEGRACAO.md    # Python-Node-React integrados
│   ├── ANALISES_MODULOS.md          # Detalhamento de análises
│   ├── GUIA_DESENVOLVIMENTO.md      # Como adicionar análises
│   ├── ESTRUTURA_PROJETO.md         # Este arquivo!
│   ├── ENDPOINTS_PYTHON.md          # Referência endpoints
│   └── SETUP_AMBIENTE.md            # Instalação/configuração
│
├── 📁 client/                        # 🎨 FRONTEND REACT (Vite)
│   ├── index.html                    # HTML raiz
│   ├── index-Enio.html              # Variante de Enio
│   ├── tsconfig.json                # TypeScript config
│   ├── .env.production              # Env produção
│   ├── vite-env.d.ts                # Tipos Vite
│   │
│   ├── 📁 public/                   # Arquivos estáticos
│   │   └── __manus__/               # Assets do MANUS
│   │
│   └── 📁 src/                      # Código-fonte React
│       ├── App.tsx                  # Componente raiz (Router)
│       ├── main.tsx                 # Entry point
│       ├── index.css                # Estilos globais
│       │
│       ├── 📁 _core/                # Infraestrutura interna
│       │   ├── hooks/               # Hooks customizados
│       │   │   ├── useAuth.ts       # Autenticação
│       │   │   └── ...
│       │   ├── providers/           # Context providers
│       │   └── lib/                 # Utilitários
│       │
│       ├── 📁 components/           # Componentes reutilizáveis
│       │   ├── ui/                  # Componentes base (Button, Input, etc)
│       │   │   ├── button.tsx
│       │   │   ├── input.tsx
│       │   │   ├── table.tsx
│       │   │   └── ...
│       │   ├── modules/             # Componentes de módulos
│       │   │   ├── Analysis.tsx
│       │   │   ├── DataTable.tsx
│       │   │   └── ...
│       │   ├── layout/              # Componentes de layout
│       │   │   ├── DashboardLayout.tsx
│       │   │   ├── Header.tsx
│       │   │   └── Sidebar.tsx
│       │   └── AIChatBox.tsx        # Chat com IA (opcional)
│       │
│       ├── 📁 hooks/                # Hooks customizados
│       │   ├── useAuth.ts
│       │   └── ...
│       │
│       ├── 📁 lib/                  # Bibliotecas e utilitários
│       │   ├── trpc.ts              # Cliente tRPC
│       │   ├── api.ts               # Chamadas API diretas
│       │   └── utils.ts             # Funções utilitárias
│       │
│       ├── 📁 pages/                # Páginas (rotas)
│       │   ├── Home.tsx
│       │   ├── AuditarCNPJ.tsx      # Módulo auditoria
│       │   ├── Extracao.tsx         # Módulo extração
│       │   ├── Tabelas.tsx          # Módulo visualização
│       │   ├── ParquetView.tsx      # Visualizador Parquet
│       │   ├── Exportar.tsx         # Módulo exportação
│       │   ├── Relatorios.tsx       # Módulo relatórios
│       │   ├── Analises.tsx         # Hub de análises
│       │   │   ├── AnaliseFaturamentoPeriodo.tsx
│       │   │   ├── AnaliseRessarcimento.tsx      # 📍 ANÁLISE 1
│       │   │   ├── AnaliseOmissaoSaida.tsx       # 📍 ANÁLISE 2
│       │   │   └── ...
│       │   ├── Configuracoes.tsx    # Página configurações
│       │   ├── ComponentShowcase.tsx
│       │   ├── NotFound.tsx         # Página 404
│       │   └── ...
│       │
│       ├── 📁 contexts/             # Contextos React
│       │   ├── AuthContext.tsx
│       │   └── ...
│       │
│       ├── 📁 const.ts              # Constantes
│       ├── 📁 const-Enio.ts        # Constantes variante Enio
│       └── 📁 types.ts              # Tipos TypeScript
│
├── 📁 server/                        # 🖥️ BACKEND NODE.JS
│   ├── index.ts                      # Entry point Express
│   ├── routers.ts                    # 📌 ROTAS TRPC (ponto central)
│   ├── db.ts                         # Setup Drizzle ORM
│   ├── storage.ts                    # Gerenciamento storage
│   ├── package.json                  # Deps específicas backend
│   │
│   ├── 📁 _core/                     # Infraestrutura
│   │   ├── index.ts                  # Express setup + proxy Python
│   │   ├── context.ts                # Contexto tRPC (autenticação)
│   │   ├── trpc.ts                   # Setup tRPC base
│   │   ├── env.ts                    # Variáveis ambiente
│   │   ├── oauth.ts                  # OAuth routes
│   │   ├── vite.ts                   # Setup Vite em dev
│   │   ├── map.ts                    # API de mapas
│   │   └── ...
│   │
│   ├── 📁 _test_utils/               # Utilitários testes
│   │   └── ...
│   │
│   ├── 📁 python/                    # 🐍 BACKEND PYTHON (FastAPI)
│   │   ├── api.py                    # 📌 ARQUIVO PRINCIPAL (1575 linhas)
│   │   │                              # Contém TODOS endpoints:
│   │   │                              # ✓ Oracle connection
│   │   │                              # ✓ Parquet operations
│   │   │                              # ✓ File system browse
│   │   │                              # ✓ Relatórios (Word/Excel)
│   │   │                              # ✓ Analytics/Análises
│   │   │
│   │   ├── gerar_relatorio.py        # Helper para gerar Word
│   │   ├── README.md                 # Documentação Python API
│   │   ├── start.sh                  # Script iniciar FastAPI
│   │   ├── requirements.txt          # Deps Python (opcional)
│   │   ├── .env                      # Env Python
│   │   └── __pycache__/              # Cache Python
│   │
│   ├── 📁 auth.logout.test.ts        # Teste autenticação
│   └── 📁 python-api.test.ts         # Testes API Python
│
├── 📁 shared/                        # 🤝 TIPOS COMPARTILHADOS
│   ├── const.ts                      # Constantes compartilhadas
│   ├── types.ts                      # Tipos TypeScript
│   └── 📁 _core/                     # Utilitários internos
│
├── 📁 cruzamentos/                   # 📊 ANÁLISES PYTHON (ponto-chave!)
│   │                                  # 🚨 As análises ficam AQUI!
│   │
│   ├── 📁 funcoes_auxiliares/        # Funções reutilizáveis
│   │   ├── __init__.py
│   │   ├── aux_calc_MVA_ajustado.py  # Cálculo MVA
│   │   ├── aux_classif_merc.py       # Classificação mercadoria
│   │   ├── aux_ST.py                 # Cálculos Substituição Tributária
│   │   ├── conectar_oracle.py        # Conexão Oracle
│   │   ├── encontrar_arquivo_cnpj.py # Busca arquivos
│   │   ├── exportar_excel.py         # Export Excel
│   │   ├── extrair_parametros.py     # Parse SQL
│   │   ├── ler_sql.py                # Leitura SQL
│   │   ├── normalizar_parquet.py     # Normalização dados
│   │   ├── salvar_para_parquet.py    # Escrita Parquet
│   │   ├── validar_cnpj.py           # Validação CNPJ
│   │   └── __pycache__/
│   │
│   ├── 📁 ressarcimento/             # 📌 ANÁLISE 1: Ressarcimento ST
│   │   ├── __init__.py               # Exports públicos
│   │   ├── carregar_dados.py         # Carrega C176, NFe, C170, Fronteira
│   │   ├── cruzar_nfe_saida.py       # Cruzamento NFe saída
│   │   ├── cruzar_nfe_ultima_entrada.py  # Cruzamento última entrada
│   │   ├── cruzar_fronteira.py       # Cruzamento fronteira/SITAFE
│   │   ├── selecionar_colunas_finais.py  # 🎯 Cálculos finais
│   │   ├── resumo_terminal.py        # Resumo em terminal
│   │   ├── resumo_mensal.py          # Agregação mensal
│   │   ├── DOCUMENTACAO.md           # Explicação técnica (120 linhas)
│   │   └── __pycache__/
│   │
│   ├── 📁 omissao_saida/             # 📌 ANÁLISE 2: Omissão Saída
│   │   ├── __init__.py
│   │   ├── analise_omissao.py        # Lógica principal
│   │   └── __pycache__/
│   │
│   └── (outras análises podem ser adicionadas aqui)
│
├── 📁 consultas_fonte/               # 📝 QUERIES SQL (Fonteiras dados)
│   ├── c100.sql                      # Registro C100 (NOTAS)
│   ├── c170_simplificada.sql         # Registro C170 (ITENS)
│   ├── c176_mensal.sql               # Registro C176 (APURAÇÃO ST)
│   ├── c176_v2.sql
│   ├── c176.sql
│   ├── dados_cadastrais.sql          # Dados empresa
│   ├── E111.sql
│   ├── fronteira.sql                 # Dados SITAFE
│   ├── NFCe.sql
│   ├── NFe_dados_ST.sql              # Dados ST em NFe
│   ├── NFe_Evento.sql                # Eventos de NFe
│   ├── NFe.sql                       # NF Eletrônica
│   ├── NFe.sql
│   ├── reg_0000.sql                  # Registro 0000
│   ├── reg_0200.sql                  # Registro 0200
│   ├── VERIF_CNPJS.sql               # Verificação CNPJ
│   └── 📁 auxiliares/                # Queries auxiliares
│
├── 📁 CNPJ/                          # 📂 DADOS POR CNPJ (Saída)
│   └── 37671507000187/               # Exemplo: CNPJ
│       ├── 📁 analises/              # Resultados análises
│       ├── 📁 arquivos_parquet/      # Parquets extraído
│       └── 📁 relatorios/            # Relatórios gerados
│
├── 📁 referencias/                   # 📚 Tabelas de referência
│   ├── auxiliar_aliq_interestaduais.sql
│   ├── mapeamento_consultas_cruzamentos.md
│   ├── 📁 CEST/                      # Classificação CEST
│   ├── 📁 cfop/                      # Códigos CFOP
│   ├── 📁 CO_SEFIN/                  # Códigos SEFIN
│   ├── 📁 codigos_tributarios/       # Códigos tributários
│   ├── 📁 efd/                       # Tabelas EFD
│   ├── 📁 Fisconforme/               # Tabelas Fisconforme
│   ├── 📁 NCM/                       # Tabelas NCM
│   └── 📁 NFe/                       # Tabelas NFe
│
├── 📁 drizzle/                       # 🗄️ MIGRAÇÕES BANCO (Drizzle ORM)
│   ├── 0000_hesitant_wolf_cub.sql   # Migração inicial
│   ├── schema.ts                     # Definição schema
│   └── 📁 meta/
│       ├── _journal.json
│       └── 0000_snapshot.json
│
├── 📁 modelos_word/                  # 📄 TEMPLATES WORD
│   └── notificacao_det.txt           # Template DET
│
├── 📁 patches/                       # 🔧 CORREÇÕES
│   └── wouter@3.7.1.patch           # Patch para wouter (router)
│
├── 📁 0_apagar/                      # 🗑️ ARQUIVOS ANTIGOS
│   ├── c100.sql
│   ├── sitafe_cest.sql
│   └── sitafe_ncm.sql
│
├── 📁 __pycache__/                   # Cache Python
│
└── 📁 .git/                          # Repositório Git
```

---

## 🔗 Fluxo de Dados Entre Pastas

```
user input (client/) 
    ↓
    → App.tsx (Router)
    → pages/Analises.tsx
    → pages/AnaliseRessarcimento.tsx (exemplo)
    ↓
api.analytics.ressarcimento.useMutation() [React hook tRPC]
    ↓
    → server/routers.ts (processa requisição tRPC)
    → Valida com Zod schema
    → Auth check (protectedProcedure)
    ↓
    → server/_core/index.ts (proxy HTTP)
    → POST http://localhost:8001/api/python/analytics/ressarcimento
    ↓
    → server/python/api.py (@app.post endpoint)
    → from cruzamentos.ressarcimento import executar_analise
    ↓
    → cruzamentos/ressarcimento/
        ├─ carregar_dados.py
        ├─ cruzar_nfe_saida.py
        ├─ cruzar_nfe_ultima_entrada.py
        ├─ cruzar_fronteira.py
        └─ selecionar_colunas_finais.py
    ↓
resultado (Parquet + JSON)
    ↓
    → CNPJ/37671507000187/analises/resultado_*.parquet
    ↓
volta para React via JSON
    ↓
exibe em tabela/gráfico (components/DataTable)
```

---

## 🏭 Onde Cada Tipo de Arquivo Fica

### Configurações
```
✓ .env (variáveis de ambiente)
✓ .gitignore
✓ tsconfig.json (TypeScript)
✓ vite.config.ts (build frontend)
✓ vitest.config.ts (testes)
✓ drizzle.config.ts (banco de dados)
✓ package.json (deps: Node)
```

### Código Frontend (React)
```
✓ client/src/pages/**/*.tsx (página por análise)
✓ client/src/components/** (componentes reutilizáveis)
✓ client/src/lib/trpc.ts (cliente tRPC)
✓ client/index.html (HTML entry)
```

### Código Backend - Orquestração (Node.js)
```
✓ server/routers.ts (rotas tRPC)
✓ server/index.ts (Express + proxy)
✓ server/_core/** (infraestrutura Auth/tRPC/OAuth)
✓ server/db.ts (Drizzle ORM)
```

### Código Backend - Processamento Pesado (Python)
```
✓ server/python/api.py (TODOS endpoints FastAPI)
✓ server/python/gerar_relatorio.py (helpers Word/Excel)
✓ server/python/start.sh (script iniciar)
```

### **Análises Python 🔑**
```
✓ cruzamentos/funcoes_auxiliares/** (compartilhadas)
✓ cruzamentos/ressarcimento/** (análise 1)
✓ cruzamentos/omissao_saida/** (análise 2)
```

### Dados Fiscais
```
✓ consultas_fonte/** (SQL para extrair)
✓ CNPJ/[CNPJ_limpo]/arquivos_parquet/** (extraído)
✓ referencias/** (tabelas de referência)
```

### Banco de Dados
```
✓ drizzle/** (migrações SQLite)
✓ drizzle/schema.ts (definição tabelas)
```

---

## 📊 Tabela de Responsabilidades

| Pasta | Responsável | O que faz | Linguagem |
|-------|-------------|----------|-----------|
| `client/` | Frontend Dev | Interface User | React/TypeScript |
| `server/` | Backend Dev | Orquestração | Node.js/TypeScript |
| `server/python/` | Data Engineer | Processamento pesado | Python |
| `cruzamentos/` | Data Scientist | Análises complexas | Python |
| `consultas_fonte/` | DBA | Extração Oracle | SQL |
| `CNPJ/[id]/` | Output | Dados processados | Parquet/JSON |
| `Referencias/` | Admin | Lookup tables | SQL/Parquet |

---

## 🎯 Arquivos-Chave

### Se quer entender:

**"Como requisições chegam ao Python?"**
→ Leia: `server/routers.ts` + `server/_core/index.ts`

**"Como uma análise funciona?"**
→ Leia: `cruzamentos/ressarcimento/DOCUMENTACAO.md`

**"Quais endpoints Python existem?"**
→ Leia: `server/python/api.py` (procure por `@app.post`)

**"Como dados são importados?"**
→ Leia: `consultas_fonte/` + `server/python/api.py` (função `extract`)

**"Como adiciono nova análise?"**
→ Siga: `documentacao/GUIA_DESENVOLVIMENTO.md`

---

## 💾 Tamanho Estimado

```
📦 Dependências (node_modules):       ~500 MB (não commitar)
📦 Dependências (venv Python):        ~300 MB (não commitar)
📦 Código-fonte:                      ~10 MB
📦 Parquets extraídos (CNPJ/*/):      ~1-5 GB por empresa
📦 Banco SQLite (sefin_audit.db):     ~1-10 MB
```

---

**Ver também:**
- [README.md](./README.md) - Índice de documentação
- [ARQUITETURA_INTEGRACAO.md](./ARQUITETURA_INTEGRACAO.md) - Fluxo Python-Node-React
- [ANALISES_MODULOS.md](./ANALISES_MODULOS.md) - Detalhes de cada análise
