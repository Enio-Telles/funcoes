# SEFIN Audit Tool 🔍

Uma ferramenta robusta e moderna de auditoria fiscal desenvolvida para a **Secretaria de Estado de Finanças (SEFIN) de Rondônia**. O foco central é a extração, manipulação e análise de dados fiscais (Oracle/SPED) com alta performance.

## 🌟 Principais Funcionalidades

- **Extração Oracle Inteligente**: Interface amigável para extrair dados por CNPJ, com suporte a *bind variables* e salvamento automático em formato Parquet.
- **Visualização de Dados Ultra-Rápida**: Navegação em milhões de linhas com Polars, filtros instantâneos e edição inline.
- **Cruzamento de Dados**: Módulo expansível para auditorias complexas (ressarcimento, confronto SPED vs XML, etc).
- **Relatórios Automatizados**: Geração de documentos em Word (Papel Timbrado SEFIN), HTML para DET e exportação Excel.

## 🚀 Tech Stack

- **Frontend**: React, TypeScript, Vite, Tailwind CSS, Framer Motion (UI/UX Premium).
- **Backend (Orquestração)**: Node.js, Express, TRPC, Drizzle ORM.
- **Backend (Dados)**: Python 3.11+, FastAPI, Polars (processamento de alto desempenho), OracleDB.
- **Banco de Dados**: MySQL (metadados) e Oracle (extração).

## 🛠️ Como Instalar e Rodar

### Requisitos
- Node.js (v18+)
- PNPM (`npm i -g pnpm`)
- Python 3.11+
- Oracle Instant Client (configurado para `oracledb`)

### Passos
1. **Clone o repositório**:
   ```bash
   git clone [url-do-repositorio]
   cd sefin-audit-tool
   ```

2. **Instale as dependências de Node**:
   ```bash
   pnpm install
   ```

3. **Configure o ambiente**:
   Crie um arquivo `.env` baseado nas configurações do `server/_core/env.ts` (Host, DB, Oracle).

4. **Inicie o servidor de desenvolvimento**:
   ```bash
   pnpm dev
   ```

## 📂 Estrutura do Projeto

- `client/`: Aplicação React (interface e componentes).
- `server/`: Servidor Express e lógica principal.
  - `python/`: Endpoints e scripts de processamento pesado de dados.
  - `_core/`: Infraestrutura, autenticação e utilitários.
- `shared/`: Tipos e esquemas compartilhados entre cliente e servidor.
- `drizzle/`: Migrações e esquemas do banco de dados MySQL.

---
*Desenvolvido para auditores, por quem entende de dados fiscais.*
