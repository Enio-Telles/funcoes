# Arquitetura do Sistema - SEFIN Audit Tool 🏗️

A ferramenta SEFIN Audit Tool foi projetada com uma arquitetura híbrida para combinar a agilidade de uma interface modernizada com a potência de processamento de dados do Python.

## 🗄️ Modelagem de Dados

### MySQL (Metadados e Usuários)
Utilizamos o **Drizzle ORM** para gerenciar o banco relacional. Atualmente, a estrutura foca em:
- **Tabela `users`**: Armazena informações de perfil, e-mail, papel (user/admin) e metadados de acesso (OAuth OpenID).
- **Extensibilidade**: O esquema está preparado para receber tabelas de logs de extração e configurações de consultas personalizadas.

### Parquet (Dados Operacionais)
Os dados fiscais não residem no MySQL para garantir performance. Eles são armazenados em arquivos `.parquet` particionados por CNPJ.
- **Vantagem**: Permite que o Polars leia apenas as colunas necessárias, reduzindo drasticamente o uso de memória.
- **Localização**: Definida na configuração de extração (geralmente uma subpasta por empresa).

## 🔄 Fluxo de Dados


A arquitetura segue o seguinte fluxo:
1. **Cliente (React)**: Solicita uma ação (ex: "Extrair Parquet") via TRPC.
2. **Servidor Node.js (Express)**: Recebe a requisição, valida a autenticação e orquestra a chamada para o Python.
3. **Servidor Python (FastAPI)**: Executa a tarefa pesada (conexão Oracle, processamento com Polars, escrita de arquivos Parquet).
4. **Armazenamento**:
   - **MySQL**: Metadados, configurações e estado da aplicação.
   - **Parquet**: Dados fiscais volumosos para consulta rápida e eficiente.
   - **Oracle Cloud/DW**: Fonte primária dos dados de auditoria.

## 🧱 Componentes Principais

### Frontend (Client)
- **Dashboard Modular**: Layout flexível baseado no padrão "Clarity Workspace".
- **TRPC Client**: Comunicação tipada e segura com o backend.
- **Framer Motion**: Micro-interações e transições fluidas.
- **TanStack Query**: Gerenciamento de estado assíncrono e cache.

### Backend Orquestrador (Node.js)
- **TRPC API**: Define os procedimentos disponíveis para o frontend.
- **Drizzle ORM**: Interação otimizada com o banco MySQL.
- **Proxy Python**: Encaminha requisições específicas de processamento de dados para o FastAPI.

### Backend de Dados (Python/FastAPI)
- **FastAPI**: Servidor leve para expor funcionalidades de ciência de dados.
- **Polars**: Substituindo o Pandas para garantir performance superior em grandes volumes de dados (SPED/NFe).
- **OracleDB**: Driver nativo para extração direta do DW da SEFIN.
- **Docx/XlsxWriter**: Geração de documentos complexos.

## 📊 Estratégia de Armazenamento Parquet

Os dados extraídos são salvos em estruturas de pastas organizadas por CNPJ:
`.../output_dir/[CNPJ_LIMPO]/[Nome_da_Consulta]_[CNPJ].parquet`

Este formato garante:
1. **Performance**: Consultas colunares extremamente rápidas.
2. **Compressão**: Economia de espaço em disco em relação ao CSV ou SQL puro.
3. **Tipagem**: Preservação dos tipos de dados originais do Oracle.

## 🔐 Segurança e Auditoria

- **Autenticação**: Baseada em cookies seguros com JWT/Jose.
- **Acesso Oracle**: Credenciais são gerenciadas no servidor, nunca expostas ao cliente.
- **Logs**: Todas as extrações e alterações em Parquet são registradas para auditoria interna.

---
*Para dúvidas técnicas, consulte o código-fonte em `/server` e `/client`.*
