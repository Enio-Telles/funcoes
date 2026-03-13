# Guia de Contribuição - SEFIN Audit Tool 🤝

Este documento orienta como desenvolvedores e auditores podem contribuir para a expansão da ferramenta.

## 🛠️ Adicionando Novos Módulos de Análise

O sistema foi desenhado para ser modular. Para adicionar um novo cruzamento de dados:

### 1. Backend Python (Lógica de Dados)
- Adicione a função de processamento em `server/python/api.py` ou crie um novo arquivo no mesmo diretório.
- Use o **Polars** (`pl.read_parquet`) para garantir performance.
- Exponha a funcionalidade via um novo endpoint FastAPI.

### 2. Backend Node.js (Orquestração)
- Se necessário, adicione uma nova rota TRPC em `server/routers.ts` que faça o proxy para o endpoint Python.
- Defina os schemas de entrada/saída usando **Zod** para garantir tipagem ponta-a-ponta.

### 3. Frontend React (Interface)
- Crie um novo componente em `client/src/components/modules/`.
- Utilize os hooks do TRPC (`api.moduleName.action.useMutation`) para interagir com os dados.
- Siga o design system baseado no **Plus Jakarta Sans** e componentes do Radix UI.

## 📏 Padrões de Código

- **TypeScript**: Use tipos estritos. Evite `any`.
- **Python**: Siga o PEP 8. Use `type hints` em todas as funções da API.
- **Commits**: Utilize mensagens claras em português (ex: `feat: adiciona módulo de ressarcimento de ST`).

## 🧪 Testes

Antes de enviar uma contribuição, verifique se os testes existentes continuam passando:
```bash
pnpm test
```

## 🏗️ Fluxo de Git

1. Crie uma branch para sua funcionalidade: `git checkout -b feat/nova-analise`.
2. Implemente e teste localmente.
3. Abra um Pull Request detalhando as mudanças e os impactos na base de dados Parquet.

---
*Sua contribuição ajuda a fortalecer a fiscalização do Estado de Rondônia!*
