# Regras de Classificação e Unificação

## Consenso de Atributos
- NCM, CEST, GTIN e Descrição podem ser inferidos por consenso entre fontes (NFe/NFCe/0200)
- Critérios sugeridos: frequência, confiabilidade da fonte, precedência (ex.: 0200 > NFe, se não conflitar)

## Conflitos e Revisão Manual
- Produtos com `requer_revisao_manual = true` devem ser tratados via UI/API
- Ações possíveis: unificar códigos, desagregar grupos, ajustar NCM/CEST/GTIN/descrições

## Chave de Produto
- `chave_produto`: identificador master; documentar como é derivada no motor de unificação

## Políticas
- Desagregar quando descrições forem semanticamente distintas com NCM/CEST conflitante
- Unificar quando variações mínimas de descrição não alterarem classificação fiscal
