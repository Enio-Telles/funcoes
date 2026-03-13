# Análises e Módulos - Documentação Detalhada 📊

Este documento detalha cada análise/cruzamento implementado no SEFIN Audit Tool, sua localização e como funciona internamente.

---

## 🗂️ Localização das Análises

```
📦 PROJETO ROOT
└── 📁 cruzamentos/              ← AQUI FICAM TODAS AS ANÁLISES
    ├── 📁 funcoes_auxiliares/   # Funções compartilhadas
    │   ├── aux_calc_MVA_ajustado.py      # Cálculo de MVA
    │   ├── aux_classif_merc.py           # Classificação de mercadoria
    │   ├── aux_ST.py                     # Cálculos ST (Substituição Tributária)
    │   ├── conectar_oracle.py            # Conexão Oracle
    │   ├── encontrar_arquivo_cnpj.py     # Busca arquivos por CNPJ
    │   ├── exportar_excel.py             # Exportação Excel
    │   ├── extrair_parametros.py         # Parse de parâmetros SQL
    │   ├── ler_sql.py                    # Leitura de arquivos SQL
    │   ├── normalizar_parquet.py         # Normalização de dados
    │   ├── salvar_para_parquet.py        # Escrita em Parquet
    │   ├── validar_cnpj.py               # Validação de CNPJ
    │   └── __pycache__/                  # Cache Python
    │
    ├── 📁 ressarcimento/         ← ANÁLISE 1: RESSARCIMENTO ICMS ST (C176 vs NFe)
    │   ├── __init__.py
    │   ├── carregar_dados.py             # Carrega C176, NFe, C170, Fronteira
    │   ├── cruzar_nfe_saida.py           # Cruzamento com NFe de saída
    │   ├── cruzar_nfe_ultima_entrada.py  # Cruzamento com última entrada
    │   ├── cruzar_fronteira.py           # Cruzamento com dados de fronteira
    │   ├── selecionar_colunas_finais.py  # Cálculo final (v_ress_st, v_ress_st_2)
    │   ├── resumo_terminal.py            # Exibe resumo no terminal
    │   ├── resumo_mensal.py              # Agregação mensal
    │   ├── DOCUMENTACAO.md               # Detalhamento técnico
    │   └── __pycache__/
    │
    └── 📁 omissao_saida/         ← ANÁLISE 2: AUDITORIA DE OMISSÃO DE SAÍDA
        ├── __init__.py
        ├── analise_omissao.py            # Lógica principal
        └── __pycache__/
```

---

## 📍 Análise 1: Ressarcimento ICMS ST (C176 vs NFe)

### 📌 Localização
```
cruzamentos/ressarcimento/
├── carregar_dados.py
├── cruzar_nfe_saida.py
├── cruzar_nfe_ultima_entrada.py
├── cruzar_fronteira.py
├── selecionar_colunas_finais.py
├── resumo_terminal.py
├── resumo_mensal.py
└── DOCUMENTACAO.md
```

### 🎯 Objetivo
Cruzar registros **C176 do SPED** (Apuração de ICMS ST) com **Notas Fiscais Eletrônicas**, identificando:
- Se as compras/vendas batem
- Valores passíveis de ressarcimento/estorno
- Diferenças entre ST informado vs calculado

### 🔄 Fluxo de Execução

```
1. carregar_dados.py
   └─> Busca arquivos: C176.parquet, NFe.parquet, C170.parquet, Fronteira.sql
   └─> Normaliza colunas (minúsculas)
   └─> Padroniza tipos de dados

2. cruzar_nfe_saida.py
   └─> Localiza NFe correspondente à SAÍDA (descrita no C176)
   └─> Tenta: (Chave + Código Produto) ou (Chave + Item C176)
   └─> Adiciona colunas de NFe ao resultado

3. cruzar_nfe_ultima_entrada.py
   └─> Localiza NFe da ÚLTIMA ENTRADA informada no C176
   └─> Passa por C170 para descobrir número do item XML correto
   └─> Traz informações de entrada ao DataFrame

4. cruzar_fronteira.py
   └─> Busca dados SITAFE (Fronteira)
   └─> Traz: co_sefin, rotina_calculo, valor_icms_fronteira
   └─> Essencial para cálculo de v_ress_st_1

5. selecionar_colunas_finais.py  ⭐ AQUI ACONTECEM OS CÁLCULOS
   ├─> Executa rateio lógico (qtde_considerada)
   ├─> Calcula v_unit_ress_st_1 = valor_icms_fronteira / prod_qcom_ult_entr_xml
   ├─> Calcula v_ress_st = v_unit_ress_st_1 * qtde_considerada
   ├─> Calcula v_ress_st_2 via MVA inferida
   └─> Consolida colunas finais

6. resumo_terminal.py
   └─> Imprime estatísticas (Rich Table)

7. resumo_mensal.py
   └─> Agrega resultados por período
```

### 📊 Valores Calculados

#### v_ress_st (Via Fronteira/SITAFE)

```
v_unit_ress_st_1 = valor_icms_fronteira / prod_qcom_ult_entr_xml
v_ress_st = v_unit_ress_st_1 * qtde_considerada
```

**Interpretação:**
- ICMS "fixo" por unidade que incidiu na entrada
- Multiplicado pela quantidade real usada

#### v_ress_st_2 (Via Inferência MVA)

```
vbc_st_calc = vprod + vfrete + vseg + voutro - vdesc + vipi
v_ress_st_2 = (vbc_st_calc * (icms_aliq_entrada / 100)) - icms_vicms_entrada
```

**Interpretação:**
- Recalcula ICMS ST como se fosse tributado internamente
- Desconta ICMS próprio já pago

### 🔧 Como Usar (via API)

```bash
# Via Python FastAPI
POST /api/python/analytics/ressarcimento
Content-Type: application/json

{
  "cnpj": "12345678000190",
  "data_ini": "2024-01-01",
  "data_fim": "2024-12-31",
  "input_dir": "C:\\dados\\37671507000187",
  "output_dir": "C:\\dados\\relatorios"
}
```

### 📝 Colunas do Resultado

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `chave_nfe_saida` | str | Chave da nota de saída |
| `prod_codigo_saida` | str | Código do produto na saída |
| `qtde_considerada` | float | Quantidade rateada (limitada) |
| `v_unit_ress_st_1` | float | Valor unitário (fronteira) |
| `v_ress_st` | float | **Ressarcimento principal (ST via fronteira)** |
| `v_ress_st_2_inferido` | float | Ressarcimento alternativo (MVA local) |
| `v_ress_st_2_fronteira` | float | Ressarcimento alternativo (MVA fronteira) |
| `status_cruzamento` | str | OK, PARCIAL, FALHA |

---

## 📍 Análise 2: Auditoria de Omissão de Saída

### 📌 Localização
```
cruzamentos/omissao_saida/
├── __init__.py
├── analise_omissao.py           # Lógica principal
└── __pycache__/
```

### 🎯 Objetivo
Identificar **notas fiscais de entrada** que não possuem correspondência em **saídas registradas**, indicando possível:
- Sonegação fiscal
- Omissão de faturamento
- Desvio de mercadoria

### 🔄 Fluxo de Execução

```
1. Carrega dados:
   ├─> NFe de ENTRADA (compras)
   ├─> NFe de SAÍDA (vendas)
   ├─> Registros SPED (C100, C170)
   └─> Parâmetros de tolerância

2. Para cada entrada:
   └─> Busca saída correspondente by:
       ├─> Chave NFe
       ├─> Código do produto
       ├─> Quantidade
       └─> Período temporal

3. Classifica como:
   ├─> ENCONTRADA (OK)
   ├─> PARCIAL (quantidade diferente)
   └─> OMITIDA (não encontrada)

4. Calcula indicadores:
   ├─> Taxa de conformidade
   ├─> Valor omitido
   ├─> ICMS em risco
   └─> Recomendação (notificar?)
```

### 📊 Saída da Análise

```python
{
  "cnpj": "12345678000190",
  "periodo": "2024-01",
  "total_entradas": 1250,
  "entradas_com_saida": 1180,
  "entradas_omissao_parcial": 35,
  "entradas_omissao_total": 35,
  "valor_omitido_icms": 45670.50,
  "taxa_conformidade": 94.4,
  "detalhes": [
    {
      "chave_entrada": "...",
      "produto": "...",
      "qtde_entrada": 100,
      "qtde_saida_encontrada": 60,
      "status": "PARCIAL",
      "icms_risco": 2350.00
    }
  ]
}
```

### 🔧 Como Usar (via API)

```bash
POST /api/python/analytics/omissao_saida
Content-Type: application/json

{
  "cnpj": "12345678000190",
  "data_ini": "2024-01-01",
  "data_fim": "2024-12-31",
  "input_dir": "C:\\dados\\37671507000187",
  "tolerancia_dias": 45,
  "tolerancia_percentual": 5.0
}
```

---

## 🧩 Pipeline de Produtos (Unificação e Revisão)

### 📌 Localização
- `server/python/routers/analysis.py` — Orquestra pipeline de produtos
- `server/python/routers/produto_unid.py` — Endpoints de revisão, unificação e desagregação
- `server/python/routers/filesystem.py` — Lista artefatos de produtos
- `server/python/routers/export.py` — Geração de Excel de revisão manual

### 🎯 Objetivo
Consolidar itens de múltiplas fontes (NFe/NFCe, SPED 0200/C170) em um produto master com NCM/CEST de consenso, sinalizando pendências para revisão manual e permitindo aplicar correções.

### 🔄 Artefatos
- `mapa_produto_nfe_{cnpj}.parquet`, `mapa_produto_0200_{cnpj}.parquet`
- `produtos_agregados_{cnpj}.parquet` (master)
- `base_detalhes_produtos_{cnpj}.parquet`
- `mapa_auditoria_{cnpj}.parquet`

### 🔧 Endpoints Relacionados
- GET `/api/python/produtos/revisao-manual` — listar pendências
- GET `/api/python/produtos/detalhes-codigo` — detalhes por código
- POST `/api/python/produtos/revisao-manual/submit` — submeter decisões
- POST `/api/python/produtos/resolver-manual-unificar|desagregar` — aplicar

Para detalhes, ver: [PRODUTOS/OVERVIEW.md](./PRODUTOS/OVERVIEW.md) e [PRODUTOS/API_SCRIPTS.md](./PRODUTOS/API_SCRIPTS.md)

## 📍 Análise 3: Faturamento por Período (Planejado)

### 📌 Status
`[Planejado]` - Estrutura em `server/python/api.py` linha ~250

### 🎯 Objetivo
Agregar dados de faturamento (NFe de saída) por período mensal/trimestral, exibindo:
- Análise de receitas
- Sazonalidade
- Comparativo com períodos anteriores

### 🔄 Fluxo
```
Carrega NFe → Agrupa por período → Calcula totalizações → Retorna série temporal
```

---

## 🔌 Como Integrar Análises com API Python

### Passo 1: Criar Endpoint em `api.py`

```python
# server/python/api.py - linha ~900 (busque "AnaliseFaturamentoRequest")

from cruzamentos.ressarcimento.analise_ressarcimento import executar_analise

@app.post("/api/python/analytics/ressarcimento")
async def analytics_ressarcimento(request: dict):
    """Executa análise de ressarcimento ICMS ST."""
    try:
        # Importa função do módulo
        from ressarcimento.analise_ressarcimento import executar_analise_ressarcimento
        
        # Executa
        resultado = executar_analise_ressarcimento(
            cnpj=request.get("cnpj"),
            data_ini=request.get("data_ini"),
            data_fim=request.get("data_fim"),
            input_dir=request.get("input_dir"),
            output_dir=request.get("output_dir")
        )
        
        return {"success": True, "data": resultado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Passo 2: Adicionar Rota tRPC em `routers.ts`

```typescript
// server/routers.ts

import { z } from "zod";

const AnalyticsRessarcimentoSchema = z.object({
  cnpj: z.string(),
  data_ini: z.string(),
  data_fim: z.string(),
  input_dir: z.string(),
  output_dir: z.string(),
});

export const appRouter = router({
  analytics: router({
    ressarcimento: protectedProcedure
      .input(AnalyticsRessarcimentoSchema)
      .mutation(async ({ input }) => {
        const response = await fetch('http://localhost:8001/api/python/analytics/ressarcimento', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(input)
        });
        
        if (!response.ok) {
          throw new TRPCError({ 
            code: "INTERNAL_SERVER_ERROR",
            message: await response.text()
          });
        }
        
        return await response.json();
      })
  })
});
```

### Passo 3: Usar em React

```tsx
// client/src/pages/AnaliseRessarcimento.tsx

import { api } from "@/lib/trpc";

export default function AnaliseRessarcimento() {
  const { mutate: executarAnalise, isPending, data, error } = 
    api.analytics.ressarcimento.useMutation();

  const handleSubmit = (cnpj: string, dataIni: string, dataFim: string) => {
    executarAnalise({
      cnpj,
      data_ini: dataIni,
      data_fim: dataFim,
      input_dir: "C:\\dados",
      output_dir: "C:\\relatorios"
    });
  };

  return (
    <div>
      {isPending && <p>⏳ Processando...</p>}
      {error && <p>❌ {error.message}</p>}
      {data && (
        <ResultadosRessarcimento 
          dados={data.data}
          cnpj={data.data.cnpj}
        />
      )}
    </div>
  );
}
```

---

## 🧬 Padrão de Estrutura para Nova Análise

Quando criar uma nova análise, siga este padrão:

```
cruzamentos/minha_nova_analise/
├── __init__.py                    # Exports principais
├── carregar_dados.py              # Carrega Parquets/Oracle
├── processar_dados.py             # Lógica de cruzamento
├── calcular_resultados.py         # Cálculos finais
├── DOCUMENTACAO.md                # Explicação técnica
└── __pycache__/

# No __init__.py
from .processar_dados import executar_analise_minha_analise
__all__ = ["executar_analise_minha_analise"]
```

---

## 📚 Referência de Funções Auxiliares

Todos estes utilities estão em `funcoes_auxiliares/` e podem ser importados:

```python
from funcoes_auxiliares.validar_cnpj import validar_cnpj
from funcoes_auxiliares.ler_sql import ler_sql
from funcoes_auxiliares.normalizar_parquet import normalizar_colunas
from funcoes_auxiliares.aux_ST import calcular_st_ajustado
from funcoes_auxiliares.encontrar_arquivo_cnpj import encontrar_arquivo
```

---

## 🎓 Estudar o Código

Para aprender como funciona:

1. **Comece por:** `cruzamentos/ressarcimento/DOCUMENTACAO.md`
2. **Depois leia:** `cruzamentos/ressarcimento/carregar_dados.py`
3. **Entenda o fluxo:** Execute `cruzamentos/ressarcimento/analise_ressarcimento.py` localmente
4. **Compare com:** `server/python/api.py` para ver como é chamado

---

## 🔍 Debug de Análises

### Modo Local (sem API)

```python
# Teste direto em Python
from pathlib import Path
import sys

sys.path.insert(0, str(Path.cwd() / "cruzamentos"))
from ressarcimento import carregar_dados

df = carregar_dados.carregar_dados_ressarcimento("12345678000190")
print(df.head())
```

### Via API FastAPI

```bash
# Terminal com Python rodando
python -m uvicorn server/python/api:app --reload

# Acessa documentação interativa
open http://localhost:8001/docs
```

---

**Ver também:**
- [GUIA_DESENVOLVIMENTO.md](./GUIA_DESENVOLVIMENTO.md) - Como adicionar nova análise
- [ENDPOINTS_PYTHON.md](./ENDPOINTS_PYTHON.md) - Lista de endpoints
- [ARQUITETURA_INTEGRACAO.md](./ARQUITETURA_INTEGRACAO.md) - Fluxo Python-Node-React
