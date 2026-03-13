# SEFIN Audit Tool - Documentação Completa 📚

Bem-vindo à documentação do **SEFIN Audit Tool**, uma ferramenta robusta e moderna de auditoria fiscal desenvolvida para a **Secretaria de Estado de Finanças (SEFIN) de Rondônia**.

## 📖 Índice de Documentação

| Documento | Descrição |
|-----------|-----------|
| [ESTRUTURA_PROJETO.md](./ESTRUTURA_PROJETO.md) | Organização completa de pastas e arquivos do projeto |
| [ARQUITETURA_INTEGRACAO.md](./ARQUITETURA_INTEGRACAO.md) | Como Python, Node.js e React se integram no sistema |
| [ANALISES_MODULOS.md](./ANALISES_MODULOS.md) | Detalhamento de cada análise/cruzamento implementado |
| [GUIA_DESENVOLVIMENTO.md](./GUIA_DESENVOLVIMENTO.md) | Como adicionar novas análises e módulos |
| [PRODUTOS/OVERVIEW.md](./PRODUTOS/OVERVIEW.md) | Visão geral do pipeline de Produtos (NCM/CEST, unificação, revisão) |
| [ENDPOINTS_PYTHON.md](./ENDPOINTS_PYTHON.md) | Referência completa dos endpoints da API Python |
| [SETUP_AMBIENTE.md](./SETUP_AMBIENTE.md) | Instruções de instalação e configuração |

---

## 🎯 Principais Funcionalidades

### ✅ Extração Oracle Inteligente
- Interface amigável para extrair dados por CNPJ
- Suporte a bind variables
- Salvamento automático em formato Parquet

### ✅ Visualização de Dados Ultra-Rápida
- Navegação em milhões de linhas com Polars
- Filtros instantâneos
- Edição inline de dados

### ✅ Cruzamento de Dados (Análises)
- **Ressarcimento ICMS ST** (C176 vs NFe)
- **Faturamento por Período** (análise de receitas)
- **Omissão de Saída** (identificação de ausências de registros)
- **Módulo Expansível** para novos cruzamentos

### ✅ Relatórios Automatizados
- Documentos em Word (Papel Timbrado SEFIN)
- Notificações DET em HTML/TXT
- Exportação Excel com formatação

---

## 🏗️ Stack Tecnológico

<table>
<tr>
  <td><strong>Frontend</strong></td>
  <td>React 19, TypeScript, Vite, Tailwind CSS, Framer Motion</td>
</tr>
<tr>
  <td><strong>Backend Orquestração</strong></td>
  <td>Node.js, Express, tRPC, Drizzle ORM</td>
</tr>
<tr>
  <td><strong>Backend Dados</strong></td>
  <td>Python 3.11+, FastAPI, Polars, OracleDB</td>
</tr>
<tr>
  <td><strong>Bancos de Dados</strong></td>
  <td>SQLite (local), MySQL (metadados), Oracle (fonte primária)</td>
</tr>
<tr>
  <td><strong>Armazenamento</strong></td>
  <td>Parquet (dados fiscais)</td>
</tr>
</table>

---

## 🚀 Quick Start

### Pré-requisitos
```bash
✓ Node.js v18+
✓ Python 3.11+
✓ PNPM (npm i -g pnpm)
✓ Oracle Instant Client (para conexão OracleDB)
✓ Conda (para gerenciar ambiente Python)
```

### Instalação
```bash
# 1. Clone e dependências Node
git clone [url-repo]
cd sefin-audit-tool
pnpm install

# 2. Crie .env na raiz (copie campos em SETUP_AMBIENTE.md)
# 3. Abra 2 terminais simultaneamente

# Terminal 1: Frontend + API Node
pnpm dev
# Acessa em http://localhost:3000

# Terminal 2: API Python
conda activate audit  # ou seu env
cd server/python
python -m uvicorn api:app --port 8001 --reload
# API Docs em http://localhost:8001/docs
```

---

## 🔄 Fluxo de Dados Resumido

```
┌─────────────────────────────────────────────────────────────┐
│                    React (Cliente)                           │
│              Requisição TRPC (ex: "Extrair")               │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Node.js + Express + tRPC                        │
│     Valida autenticação, orquestra chamada Python            │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Python FastAPI (Dados Pesados)                  │
│   ✓ Conexão Oracle (Polars)                                 │
│   ✓ Leitura/Escrita Parquet                                 │
│   ✓ Análises complexas (cruzamentos)                        │
│   ✓ Geração de relatórios (Word/Excel)                      │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Armazenamento de Dados                          │
│   • Parquet (dados fiscais volumosos)                        │
│   • SQLite/MySQL (metadados & configurações)                │
│   • Oracle (fonte primária)                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📂 Estrutura de Pastas Principais

```
sefin-audit-tool/
├── documentacao/              👈 VOCÊ ESTÁ AQUI
│   ├── README.md
│   ├── ESTRUTURA_PROJETO.md
│   ├── ARQUITETURA_INTEGRACAO.md
│   ├── ANALISES_MODULOS.md
│   ├── GUIA_DESENVOLVIMENTO.md
│   └── ...
├── client/                    # Frontend React (Vite)
│   └── src/
│       ├── pages/            # Página de Análises em /analises/*
│       ├── components/       # Componentes reutilizáveis
│       └── lib/
├── server/
│   ├── python/               # 🐍 Backend Python (FastAPI)
│   │   ├── api.py           # Endpoints principais
│   │   ├── gerar_relatorio.py
│   │   └── start.sh
│   ├── routers.ts            # Rotas tRPC (Node.js)
│   ├── index.ts              # Express + Proxy Python
│   └── _core/
├── cruzamentos/              # 📊 Módulos de Análises
│   ├── funcoes_auxiliares/   # Funções reutilizáveis
│   ├── ressarcimento/        # C176 vs NFe
│   └── omissao_saida/        # Auditoria omissão
└── shared/                   # Tipos compartilhados
```

---

## ⚡ Conceitos-Chave

### FastAPI + Python para Análises
O backend Python é responsável por:
- Executar queries complexas no Oracle
- Processar dados volumosos com Polars
- Realizar cruzamentos e análises
- Gerar relatórios Word/Excel

### tRPC para Orquestração
O Node.js atua como orquestrador:
- Define rotas tRPC (tipo-seguras)
- Autentica requisições
- Faz proxy para Python (quando necessário)

### Parquet para Performance
Dados fiscais são armazenados em Parquet:
- Leitura colunar (apenas colunas necessárias)
- Compressão automática
- Preservação de tipos de dados

### Análises Modulares
Cada análise fica em sua pasta dentro de `cruzamentos/`:
```
cruzamentos/
├── ressarcimento/
│   ├── carregar_dados.py
│   ├── cruzar_nfe_saida.py
│   ├── selecionar_colunas_finais.py
│   └── DOCUMENTACAO.md
├── omissao_saida/
│   ├── analise_omissao.py
│   └── ...
```

---

## 📖 Próximas Leituras

6. Produtos → [PRODUTOS/OVERVIEW.md](./PRODUTOS/OVERVIEW.md)

1. **Iniciante?** → Leia [SETUP_AMBIENTE.md](./SETUP_AMBIENTE.md)
2. **Quer entender a arquitetura?** → [ARQUITETURA_INTEGRACAO.md](./ARQUITETURA_INTEGRACAO.md)
3. **Precisa conhecer as análises?** → [ANALISES_MODULOS.md](./ANALISES_MODULOS.md)
4. **Quer adicionar uma análise?** → [GUIA_DESENVOLVIMENTO.md](./GUIA_DESENVOLVIMENTO.md)
5. **Precisa de referência de endpoints?** → [ENDPOINTS_PYTHON.md](./ENDPOINTS_PYTHON.md)

---

## 🤝 Contribuindo

O projeto foi desenhado para ser modular e expansível. Veja [GUIA_DESENVOLVIMENTO.md](./GUIA_DESENVOLVIMENTO.md) para instruções de:
- ✅ Adicionar novas análises
- ✅ Criar novos endpoints Python
- ✅ Adicionar componentes React para análises
- ✅ Padrões de código e best practices

---

## 📞 Suporte

Para dúvidas técnicas:
- Consulte a documentação específica do módulo
- Verifique os comentários no código-fonte
- Execute `python -m uvicorn api:app --reload` para explorar endpoints com Swagger

---

**Desenvolvido com ❤️ para auditores que entendem de dados fiscais.**
