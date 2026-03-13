Atue como um Engenheiro de Dados e Desenvolvedor Full-Stack. Preciso criar uma sistemática com interface (UI) e lógica de backend para a análise, agregação e desagregação manual de produtos fiscais.

Abaixo estão os requisitos, fontes de dados e regras de negócio detalhadas:

# 1. OBJETIVO PRINCIPAL
Analisar a tabela `produtos` linha a linha, filtrando apenas os registros onde `requer_revisao_manual = true`. O sistema deve permitir que o usuário decida se deseja "Agregar" ou "Desagregar" as informações daquela linha, substituindo o registro original pelos novos registros gerados.

# 2. FONTES DE DADOS (Arquivos de Referência)
O sistema deve ler os seguintes arquivos para enriquecer a visualização do usuário:
* `tabela_ncm.parquet`: Contém `Capitulo` (com `Descr_Capitulo`), `Posicao` (com `Descr_Posicao`) e `Codigo_NCM` (com `Descricao`).
* `segmentos_mercadorias.parquet`: Contém `Codigo_Segmento` e `Nome_Segmento`.
* `cest.parquet`: Contém o `CEST`, uma lista dos `NCMs` vinculados a este CEST e uma lista de `DESCRICAO`.

# 3. INTERFACE PRINCIPAL (Tabela de Revisão)
* Apresentar os produtos que requerem revisão em formato de lista/tabela.
* Ao lado de cada linha, deve haver obrigatoriamente dois botões: **[Agregar]** e **[Desagregar]**.

# 4. COMPORTAMENTO DO POP-UP (Ao clicar em Agregar ou Desagregar)
Ao clicar em qualquer um dos botões, abrir uma janela pop-up com as seguintes características:
* **Exibição Fiel:** Mostrar as características do produto (`codigos`, `descricoes`, `descr_compl`, `ncms`, `cest`, `gtin`) exatamente da forma, ordem e unidades originais que aparecem nos registros fiscais (NFe, Bloco H e C170).
* **Enriquecimento Visual (Tooltips/Info):** Sempre que um código NCM ou CEST for exibido, o sistema deve mostrar uma explicação detalhada baseada nos arquivos `.parquet` citados na Seção 2.
    * *Para NCM:* Mostrar a hierarquia (Capítulo + Descrição -> Posição + Descrição -> Código NCM + Descrição).
    * *Para CEST:* Mostrar o Segmento (Código + Nome do segmento) e os dados do `cest.parquet` (lista de NCMs e Descrições vinculadas àquele CEST).

# 5. REGRAS DE NEGÓCIO E LÓGICA DE TRANSFORMAÇÃO

**Regra A: Dinâmica de Seleção e Desagregação Complexa**
* O pop-up deve permitir a *seleção individual* de cada característica exibida.
* É crucial suportar cenários complexos de separação. Exemplo: Uma linha possui 3 descrições aglutinadas. O usuário deve conseguir selecionar 2 descrições para continuarem "agregadas" em um produto, e selecionar 1 descrição para ser "desagregada" em um produto totalmente novo.
* Para cada produto novo gerado através da desagregação, o sistema deve **gerar um novo código de produto**.

**Regra B: Lógica de Agregação de Unidades**
* Quando o usuário confirmar uma agregação de itens, as unidades de medida originais desses itens devem ser consolidadas e salvas dentro de uma lista chamada `lista_unid`.

**Regra C: Atualização da Base de Dados**
* As ações finalizadas no pop-up (seja o resultado de uma agregação ou os múltiplos resultados de uma desagregação) devem obrigatoriamente **substituir a linha original** na tabela `produtos`, atualizando o status de revisão.