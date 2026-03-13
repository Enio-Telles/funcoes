# Guia Rápido: Instalação e Uso 🚀

Este guia fornece os passos essenciais para colocar o **SEFIN Audit Tool** em funcionamento rapidamente.

## 1. Pré-requisitos 📋

Antes de começar, instale:
- [Node.js v18+](https://nodejs.org/)
- [Python 3.11+](https://www.python.org/)
- [PNPM](https://pnpm.io/installation): `npm i -g pnpm`
- [Oracle Instant Client](https://www.oracle.com/database/technologies/instant-client/downloads.html) (Necessário para a biblioteca `oracledb`).

## 2. Instalação e Configuração 🛠️

### Passo 1: Dependências do Sistema
Na raiz do projeto, instale as dependências do Node e do Python:

```bash
# Instalar dependências do Frontend e Backend Node
pnpm install

# Instalar dependências do Backend Python
pip install polars oracledb fastapi uvicorn python-docx openpyxl xlsxwriter
```

### Passo 2: Variáveis de Ambiente
Crie um arquivo `.env` na raiz com as seguintes configurações básicas (ajuste conforme seu ambiente):

```env
DATABASE_URL=mysql://usuario:senha@localhost:3306/sefin_audit
PYTHON_API_PORT=8001
PORT=3000
```

## 3. Execução 🏃‍♂️

O projeto requer **dois servidores** rodando simultaneamente: o Node.js (frontend + orquestração) e o Python (processamento de dados).

### Terminal 1 — Servidor Node.js (Frontend + API)
```powershell
pnpm dev
```
- **Frontend**: [http://localhost:3000](http://localhost:3000)

### Terminal 2 — Servidor Python (FastAPI)
Abra um **novo terminal** e execute:
```powershell
conda activate extrator
cd server/python
python -m uvicorn api:app --host 0.0.0.0 --port 8001 --reload
```
- **API Python (Docs)**: [http://localhost:8001/docs](http://localhost:8001/docs)

> [!IMPORTANT]
> O servidor Python **deve estar rodando** para que as funcionalidades de extração Oracle, leitura de Parquet e exportação funcionem. Sem ele, o terminal do Node exibirá `[Python Proxy Error] fetch failed`.

## 4. Fluxo de Uso Básico 🔄

Siga estes passos para sua primeira auditoria:

1. **Configuração Oracle**: Acesse o módulo de Configurações e insira suas credenciais do DW SEFIN. Teste a conexão.
2. **Extração de Dados**:
   - Vá para o módulo de Extração.
   - Insira o **CNPJ** da empresa.
   - Selecione as consultas SQL desejadas (C100, C170, etc.).
   - Clique em **Iniciar Extração**. Os dados serão salvos localmente em formato Parquet.
3. **Análise e Filtros**:
   - No módulo de Visualização, abra o arquivo Parquet gerado.
   - Utilize a barra de pesquisa para filtrar itens, valores ou CFOPs instantaneamente.
4. **Geração de Relatório**:
   - Após analisar, utilize o módulo de Relatórios para gerar a notificação DET (HTML/TXT) ou o Relatório em Papel Timbrado (Word).

---
> [!TIP]
> Em caso de erro na conexão Oracle, verifique se o **TNS_ADMIN** está configurado ou se o Host do DW é acessível pela sua rede (VPN SEFIN).

Para detalhes avançados, consulte o [README.md](./README.md) e o [ARCHITECTURE.md](./ARCHITECTURE.md).
