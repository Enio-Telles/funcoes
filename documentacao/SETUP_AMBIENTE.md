# Setup e Configuração do Ambiente 🛠️

Guia completo para instalar, configurar e colocar o SEFIN Audit Tool em funcionamento.

---

## 🎯 Visão Geral do Setup

Você precisa de **2 servidores** rodando simultaneamente:

1. **Frontend + Backend Node.js** (porta 3000)
   - React (Vite)
   - Express + tRPC

2. **Backend Python** (porta 8001)
   - FastAPI
   - Polars
   - Oracle client

---

## 📋 Pré-requisitos do Sistema

### Windows 10/11 (Recomendado para este projeto)

#### ✅ Obrigatório

- **Node.js v18+** - [Download](https://nodejs.org/)
  ```bash
  node --version  # Verifique
  ```

- **Python 3.11+** - [Download](https://www.python.org/)
  ```bash
  python --version  # Verifique
  ```

- **Conda** (Anaconda ou Miniconda) - [Download](https://www.anaconda.com/)
  ```bash
  conda --version  # Verifique
  ```

- **PNPM** - Instale via npm:
  ```bash
  npm install -g pnpm
  pnpm --version  # Verifique
  ```

- **Oracle Instant Client** (para oracledb)
  - [Download](https://www.oracle.com/database/technologies/instant-client/downloads.html)
  - Extraia em local acessível
  - Adicione ao PATH do Windows ou configure TNS_ADMIN

#### ⚙️ Configurações Recomendadas

- **Git** - [Download](https://git-scm.com/)
- **VS Code** - [Download](https://code.visualstudio.com/)
- **Postman** ou **Insomnia** (opcional, para testar APIs)

---

## 🚀 Instalação Passo-a-Passo

### Passo 1: Clone o Repositório

```bash
git clone [url-do-repositorio]
cd sefin-audit-tool
```

### Passo 2: Instale Dependências Node.js

```bash
# Limpe cache (if issues)
pnpm store prune

# Instale deps
pnpm install

# Verifique
pnpm list --depth=0
```

### Passo 3: Configure Ambiente Python

#### 3a. Crie Ambiente Conda

```bash
# Crie ambiente
conda create -n audit python=3.11 -y

# Ative
conda activate audit

# Verifique
python --version
```

#### 3b. Instale Dependências Python

```bash
# Ative ambiente se não está
conda activate audit

# Instale bibliotecas principais
pip install --upgrade pip

# Instale pacotes
pip install polars oracledb fastapi uvicorn python-docx openpyxl xlsxwriter pyarrow python-multipart
```

**⚠️ Se falhar no `oracledb`:**
- Verifique se Oracle Instant Client está instalado
- Configure `TNS_ADMIN` → caminho para `network/admin` do Oracle
- Ou use `python-oracledb` (fallback)

```bash
pip install python-oracledb  # Fallback
```

### Passo 4: Configure Variáveis de Ambiente

Crie arquivo `.env` na raiz com:

```env
# ============================================
# NODE.JS BACKEND
# ============================================
DATABASE_URL=file:./sefin_audit.db
PYTHON_API_PORT=8001
PORT=3000
NODE_ENV=development

# ============================================
# OAUTH (Opcional - mocks por padrão)
# ============================================
OAUTH_SERVER_URL=http://localhost:3000/mock-oauth
VITE_OAUTH_PORTAL_URL=http://localhost:3000/mock-oauth
VITE_APP_ID=sefin-audit-tool

# ============================================
# ANALYTICS (Opcional)
# ============================================
VITE_ANALYTICS_ENDPOINT=mock-endpoint
VITE_ANALYTICS_WEBSITE_ID=mock-id

# ============================================
# CREDENCIAIS ORACLE (Ajuste conforme seu env)
# ============================================
ORACLE_HOST=exa01-scan.sefin.ro.gov.br
ORACLE_PORT=1521
ORACLE_SERVICE=sefindw
ORACLE_USER=seu_usuario
ORACLE_PASSWORD=sua_senha

# ============================================
# CAMINHOS LOCAIS
# ============================================
DATA_DIR=C:\\Users\\seu_usuario\\Documents\\sefin-data
OUTPUT_DIR=C:\\Users\\seu_usuario\\Documents\\sefin-output
```

---

## ▶️ Executar o Projeto

### Opção A: Executar Manualmente (2 Terminais)

#### Terminal 1: Frontend + Backend Node.js

```bash
# Ative Node environment
pnpm dev

# Esperado:
# ✓ Vite dev server rodando em http://localhost:3000
# ✓ Express + tRPC disponível em http://localhost:3000/api/trpc
```

#### Terminal 2: Backend Python

```bash
# Ative ambiente Python
conda activate audit

# Vá para diretório Python
cd server/python

# Inicie FastAPI
python -m uvicorn api:app --host 0.0.0.0 --port 8001 --reload

# Esperado:
# ✓ FastAPI rodando em http://localhost:8001
# ✓ Swagger UI em http://localhost:8001/docs
# ✓ ReDoc em http://localhost:8001/redoc
```

### Opção B: Usando Script Main (Windows)

```bash
# Na raiz do projeto
python main.py

# Isso abre 2 janelas de terminal automaticamente
```

---

## ✅ Verificação de Instalação

### 1. Frontend React

Abra [http://localhost:3000](http://localhost:3000) no navegador.

**Esperado:** Interface SEFIN Audit Tool carregada

### 2. API Node.js (tRPC)

Execute no terminal:

```bash
curl http://localhost:3000/api/trpc
```

**Esperado:** Resposta JSON (pode ser erro 404, o importante é conexão)

### 3. API Python (FastAPI)

Abra [http://localhost:8001/docs](http://localhost:8001/docs)

**Esperado:** 
- Swagger UI com lista de endpoints
- Botão "Try it out" funcionando
- ✓ Health check: `GET /api/python/health` retorna `{"status":"ok"}`

### 4. Banco SQLite

```bash
# Verifique se arquivo foi criado
ls -la sefin_audit.db  # Linux/Mac
dir sefin_audit.db     # Windows - cmd
```

**Esperado:** Arquivo ~1-10 MB criado

---

## 🔧 Configurações Avançadas

### Oracle Instant Client (Obrigatório para Extração)

#### Windows

1. **Download**
   - Acesse [Oracle Downloads](https://www.oracle.com/database/technologies/instant-client/downloads.html)
   - Selecione "Windows (x86-64)" ou "Windows (x86)"
   - Baixe arquivo .zip (não o installer)

2. **Extrair**
   ```bash
   # Exemplo
   C:\oracle\instantclient_21_7\
   ```

3. **Configurar PATH**
   - Adicione em variáveis de ambiente do Windows:
   ```
   PATH=C:\oracle\instantclient_21_7;%PATH%
   ```

4. **Testar**
   ```bash
   sqlplus -version
   # Ou
   python -c "import oracledb; print('OK')"
   ```

### Conda com Proxy Corporativo

Se estiver atrás de firewall:

```bash
# Configure conda
conda config --set proxy_servers.http http://proxy:port
conda config --set proxy_servers.https https://proxy:port

# Para pip
pip install --proxy [user:passwd@]proxy.server:port package
```

### Virtual Env (Alternativa ao Conda)

Se prefere não usar Conda:

```bash
# Crie venv
python -m venv venv_audit

# Ative
# Windows
venv_audit\Scripts\activate
# Linux/Mac
source venv_audit/bin/activate

# Instale deps
pip install -r server/python/requirements.txt
```

---

## 🐛 Troubleshooting

### ❌ "Python API unavailable: fetch failed"

**Causa:** Servidor Python não está rodando ou porta 8001 está ocupada

**Solução:**
```bash
# Terminal 2 - Verifique porta
netstat -ano | findstr :8001  # Windows

# Mate processo se necessário
taskkill /PID [PID] /F

# Ou use porta diferente
python -m uvicorn api:app --port 8002
```

### ❌ "ModuleNotFoundError: No module named 'oracledb'"

**Causa:** Dependências Python não instaladas

**Solução:**
```bash
conda activate audit
pip install oracledb

# Se ainda não funcionar:
pip install --upgrade oracledb
```

### ❌ "EADDRINUSE: address already in use :::3000"

**Causa:** Porta 3000 já em uso

**Solução:**
```bash
# Mate processo
netstat -ano | findstr :3000    # Windows
taskkill /PID [PID] /F

# Ou mude porta em .env
PORT=3001
```

### ❌ "Cannot connect to Oracle: ORA-xxxxx"

**Causa:** Conexão Oracle ou credenciais inválidas

**Solução:**
```bash
# Verifique .env
# ORACLE_HOST, ORACLE_USER, ORACLE_PASSWORD

# Teste conexão direta
sqlplus seu_usuario/sua_senha@exa01-scan.sefin.ro.gov.br:1521/sefindw

# Se não conecta, problema é infraestrutura (VPN, rede, etc)
```

### ❌ "pnpm: command not found"

**Causa:** pnpm não instalado globalmente

**Solução:**
```bash
npm install -g pnpm
pnpm --version

# Ou use npm
npm install
npm run dev
```

### ❌ "Cannot find module '@trpc/server'"

**Causa:** Dependências Node incompletas

**Solução:**
```bash
# Limpe e reinstale
rm -r node_modules pnpm-lock.yaml
pnpm install

# Ou
pnpm install --force
```

---

## 📊 Estrutura .env Completa

```env
# ================================================
# BANCO DE DADOS
# ================================================
# SQLite (local, padrão)
DATABASE_URL=file:./sefin_audit.db

# MySQL (se quiser mudar para MySQL)
# DATABASE_URL=mysql://user:password@localhost:3306/sefin_audit

# ================================================
# SERVIDORES
# ================================================
PORT=3000                           # Node.js frontend
PYTHON_API_PORT=8001               # FastAPI backend
NODE_ENV=development               # development|production

# ================================================
# AUTENTICAÇÃO OAUTH (Opcional)
# ================================================
OAUTH_SERVER_URL=http://localhost:3000/mock-oauth
VITE_OAUTH_PORTAL_URL=http://localhost:3000/mock-oauth
VITE_APP_ID=sefin-audit-tool

# ================================================
# ORACLE
# ================================================
ORACLE_HOST=exa01-scan.sefin.ro.gov.br
ORACLE_PORT=1521
ORACLE_SERVICE=sefindw
ORACLE_USER=seu_usuario
ORACLE_PASSWORD=sua_senha

# Ou use TNS
TNS_ADMIN=C:\\oracle\\network\\admin

# ================================================
# CAMINHOS
# ================================================
DATA_INPUT_DIR=C:\\dados\\entrada
DATA_OUTPUT_DIR=C:\\dados\\saida
TEMP_DIR=C:\\temp

# ================================================
# ANALYTICS
# ================================================
VITE_ANALYTICS_ENDPOINT=http://seu-analytics
VITE_ANALYTICS_WEBSITE_ID=seu_id

# ================================================
# DEBUG
# ================================================
DEBUG=*                            # Ativa logs detalhados
LOG_LEVEL=info                     # debug|info|warn|error
```

---

## 🧪 Testes

### Testes Node.js

```bash
# Roda testes vitest
pnpm test

# Watch mode
pnpm test:watch

# Coverage
pnpm test:coverage
```

### Testes Python (API)

```bash
# Dentro do ambiente conda
cd server/python

# Teste health check
curl http://localhost:8001/api/python/health

# Teste validação CNPJ
curl http://localhost:8001/api/python/validate-cnpj?cnpj=11222333000181
```

---

## 🚢 Deploy em Produção

### Build Frontend

```bash
pnpm build

# Output em dist/
```

### Iniciar em Produção

```bash
# Node.js
NODE_ENV=production pnpm preview

# Python (sem --reload)
python -m uvicorn api:app --host 0.0.0.0 --port 8001
```

---

## 📞 Checklist de Setup Completo

- [ ] ✅ Node.js v18+ instalado
- [ ] ✅ Python 3.11+ instalado
- [ ] ✅ Conda/Miniconda instalado
- [ ] ✅ PNPM instalado globalmente
- [ ] ✅ Oracle Instant Client no PATH (opcional, se usar Oracle)
- [ ] ✅ Repo clonado
- [ ] ✅ `pnpm install` executado com sucesso
- [ ] ✅ Ambiente conda criado (`audit`)
- [ ] ✅ Deps Python instaladas
- [ ] ✅ `.env` criado na raiz
- [ ] ✅ Verifique `PORT`, `PYTHON_API_PORT` não estão em uso
- [ ] ✅ Terminal 1: `pnpm dev` rodando
- [ ] ✅ Terminal 2: `python -m uvicorn api:app` rodando
- [ ] ✅ Frontend acessível em http://localhost:3000
- [ ] ✅ FastAPI Swagger em http://localhost:8001/docs
- [ ] ✅ Teste health check retorna `{"status":"ok"}`

---

## 🎓 Próximos Passos

1. **Explorar Interface** - Navegue pela UI em http://localhost:3000
2. **Testar Extração** - Configure credenciais Oracle e teste
3. **Entender Análises** - Leia [ANALISES_MODULOS.md](./ANALISES_MODULOS.md)
4. **Adicionar Análise** - Siga [GUIA_DESENVOLVIMENTO.md](./GUIA_DESENVOLVIMENTO.md)

---

**Ver também:**
- [README.md](./README.md) - Visão geral
- [ARQUITETURA_INTEGRACAO.md](./ARQUITETURA_INTEGRACAO.md) - Como tudo se conecta
- [ENDPOINTS_PYTHON.md](./ENDPOINTS_PYTHON.md) - Referência de endpoints
