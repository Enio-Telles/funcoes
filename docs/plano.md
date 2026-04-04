# Plano de Melhorias — Interface Gráfica e Visualização de Tabelas

## Resumo

Este documento consolida o plano de melhorias da interface gráfica do Fiscal Parquet Analyzer, focado em UX e visualização de tabelas.

## Melhorias Implementadas (Fase 1-2)

### ✅ Formatação Contextual de Tipos
- NCM: `12345678` → `12.34.56.78`
- CEST: `1234567` → `12.345.67`
- CNPJ: `12345678000190` → `12.345.678/0001-90`
- GTIN: blocos espaçados
- **Arquivo**: `src/utilitarios/text.py`

### ✅ Indicadores Visuais de Dados Ausentes
- Células nulas com fundo cinza claro
- Resolvers: `resolver_fundo_nulo()`
- **Arquivo**: `src/interface_grafica/utils/visual_helpers.py`

### ✅ Validação de Intervalo de Datas
- Impede data_fim < data_ini automaticamente
- Aplicado em mov_estoque, produtos_selecionados, nfe_entrada
- **Arquivo**: `src/interface_grafica/utils/ui_helpers.py`

### ✅ Atalhos de Teclado
| Atalho | Ação |
|--------|------|
| `Ctrl+F` | Focar busca |
| `Ctrl+L` | Limpar filtros |
| `Ctrl+E` | Exportar Excel |
| `Ctrl+Shift+D` | Destacar tabela |
| `Ctrl+R` | Recarregar |
| `Ctrl+Shift+K` | Fio de Ouro |

### ✅ Tooltips de Coluna
- 40+ colunas com descrições fiscais
- Aplicado via `aplicar_tooltips_tabela()`

### ✅ Amostragem para Resize
- `resizeColumnsWithSample()` limita largura 40px-420px
- Evita travamento em tabelas grandes

### ✅ Congelamento de Colunas
- Menu de contexto: "Fixar colunas-chave à esquerda"
- Reorganiza colunas importantes para início

## Pendente (Fases 3-4)

- [ ] Sincronização de seleção entre abas de estoque
- [ ] Histórico de filtros recentes
- [ ] Filtros salvos por nome
- [ ] Indicador de carregamento
- [ ] Barra de status aprimorada
- [ ] Colorir mov_estoque por tipo de operação
- [ ] Agrupar visualmente por ano

## Arquivos Criados/Modificados

| Arquivo | Status | Descrição |
|---------|--------|-----------|
| `src/utilitarios/text.py` | Modificado | Formatação contextual |
| `src/interface_grafica/utils/__init__.py` | Criado | Exportações |
| `src/interface_grafica/utils/ui_helpers.py` | Criado | Atalhos, validação, tooltips |
| `src/interface_grafica/utils/visual_helpers.py` | Criado | Resolvers de estilo |

---

*Última atualização: 03/04/2026*
