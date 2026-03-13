# Guia Operacional: Agrupamento, Desagregação e Conversão (Versão 11)

Este guia detalha o funcionamento técnico e operacional do motor de saneamento de dados do sistema, cobrindo os processos de limpeza cadastral e normalização física.

---

## 1. 🔄 Agrupamentos (De/Para Simples)

**Objetivo:** Unificar múltiplos códigos que representam o mesmo produto físico (fragmentação de estoque).

### Mecanismo Técnico
- **Função:** `ProductGrouper.add_group(target, sources)`
- **Lógica de Compressão de Caminho (Path Compression):** O sistema garante que o mapeamento seja sempre direto. Se `A → B` e você mapeia `B → C`, o sistema reescreve automaticamente para `A → C`.
- **Persistência:** Salvo no objeto `"mapa"` do arquivo `mapa_produtos.json`.
- **Aplicação:** Realizada no início do pipeline (`extracao.py`). O campo `codigo_produto_ajustado` substitui o original para todos os cálculos subsequentes.

---

## 2. ✂️ Desagregações (Mapeamento Composto)

**Objetivo:** Separar identidades distintas que compartilham o mesmo código por erro de cadastro ou reaproveitamento.

### Mecanismo de Chave Composta
- **Chave:** `CÓDIGO_ORIGINAL | DESCRIÇÃO_PRODUTO`
- **Exemplo:** 
    - `101 | SABÃO EM PÓ 1KG` → Código Virtual: `101` (Mestre)
    - `101 | DETERGENTE LÍQUIDO` → Código Virtual: `101_DET`
- **Regras de Prioridade (Eleição do Mestre):**
    1. Registro **H010** (Inventário oficial no EFD) é prioridade absoluta.
    2. Se não houver H010, a **primeira ocorrência real** (não gerada) no período é eleita como a descrição "dona" do código original.

---

## 3. 🔍 Problemas Cadastrais: Discrepâncias, Duplicidades e Coincidências

O sistema categoriza falhas de cadastro em três níveis de complexidade:

### A. Discrepâncias (Um-para-Muitos)
- **Definição:** Um único código associado a duas ou mais descrições significativamente diferentes.
- **Identificação:** `identify_code_discrepancies`.
- **Filtro de Ruído:** O sistema ignora descrições marcadas como "Estoque Zero (Gerado)", focando apenas em movimentações reais.
- **Resolução:** Requer **Desagregação**.

### B. Duplicidades (Muitos-para-Um)
- **Definição:** Múltiplos códigos para a mesma descrição de produto.
- **Identificação:** `identify_description_duplicates` e `suggest_groups_smart`.
- **Lógica de Sugestão:**
    - **Fase 1 (Vetorizada):** Busca rápida por NCM + CEST + GTIN idênticos (**GTIN Golden Key**, 99% de confiança).
    - **Fase 2 (Fuzzy):** Comparação de strings (*Levenshtein distance*) dentro de blocos do mesmo grupo NCM.
- **Resolução:** Requer **Agrupamento**.

### C. Coincidências (Overlaps)
- **Definição:** Casos críticos onde um produto aparece simultaneamente em uma Discrepância e em uma Duplicidade. 
- **Exemplo:** O Código A tem as descrições "Arroz" e "Feijão" (Discrepância), e a descrição "Arroz" também aparece no Código B (Duplicidade).
- **Ação:** Devem ser os primeiros itens a serem resolvidos, pois afetam a integridade de múltiplos SKUs.

---

## 4. ⚖️ Análise de Fatores de Conversão

A normalização de unidades garante que compras em "CAIXA" e vendas em "UNIDADE" sejam subtraídas corretamente do estoque.

### O Processo de Cálculo (`conversao.py`)
1. **Eleição da Referência:** Para cada produto/ano, a unidade com maior número de ocorrências no EFD é definida como referência (`unid_ref`).
2. **Cálculo do Fator:** 
   `Fator = Preço Médio (Unidade X) / Preço Médio (Unidade Referência)`
3. **Aplicação:**
   - `Quantidade Convertida = Qtd Original * Fator`
   - `Preço Unitário Convertido = Preço Original / Fator`

### Detector de Erros (`ConversionErrorDetector`)
O sistema analisa os fatores calculados e emite alertas baseados em:
- **Fatores Extremos:** Valores > 1000 ou < 0.001 (sugerem erro de digitação de preço ou unidade errada).
- **Variação de Preço Alta:** Fator max/min > 5.0 dentro do mesmo produto.
- **Inconsistência de Unidade:** Coeficiente de Variação (CV) dos preços > 50% para a mesma unidade (indica mistura de produtos sob o mesmo código).
- **Múltiplas Unidades:** Mais de 5 tipos de unidades para um único SKU (sugere falta de padronização no cadastro).

---

## 💡 Boas Práticas de Operação

1. **Sempre Resolver Coincidências Primeiro:** Elas são a raiz de erros em cascata no custo médio.
2. **Verificar NCM em Discrepâncias:** Se o NCM mudou junto com a descrição, a desagregação é obrigatória.
3. **Cuidado com Unidades Genéricas:** Se um produto usa "UN" e "KG" alternadamente com preços similares, o fator será próximo a 1.0, mas verifique se a conversão física faz sentido.
4. **Processar Tudo:** Após qualquer alteração no Mapeamento ou resolução de Duplicidades, o botão **"Processar Tudo"** deve ser acionado para que os novos fatores e saldos sejam calculados com base na nova estrutura unificada.
