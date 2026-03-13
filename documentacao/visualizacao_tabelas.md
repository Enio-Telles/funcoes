# Visualização de Tabelas — Análise e Propostas

Este documento descreve as funcionalidades existentes do módulo de visualização de tabelas (Parquet) no projeto, seu fluxo client ↔ server, decisões de design observadas, pontos fortes e limitações. Ao final, apresenta melhorias propostas e um roadmap de implementação.


## Visão Geral
- Página principal: client/src/pages/Tabelas.tsx ("Visualizar Tabelas").
- Viewer focado em arquivos Parquet locais (seleção por diretório ou recentes). Também suporta deep-link via /tabelas/view?file_path=...
- Renderização manual de tabela HTML com virtualização de linhas (@tanstack/react-virtual), permitindo desempenho com grande volume (page_size 100000 carregado para edição local).
- Exportação direta do arquivo Parquet para Excel via endpoint Python.
- Integrações específicas com fluxos de auditoria (agregação/desagregação por CNPJ quando há coluna codigo_original).


## Funcionalidades Existentes

1) Navegação/Seleção de Arquivos
- Seleção de diretório manual + diálogo de navegação de pastas (FolderBrowserDialog).
- Lista de arquivos Parquet do diretório com: nome relativo, tamanho humano, linhas, botão para abrir em nova aba.
- Histórico de diretórios recentes, com remoção individual e reuso.
- Acesso rápido às Referências (paths.referencias → referências/NCM/CEST etc.).

2) Carregamento e Renderização de Tabela
- Carrega conteúdo inteiro do Parquet via POST /api/python/parquet/read (Polars) com filtros/ordenação server-side opcionais; na página Tabelas, o padrão atual é carregar até 100000 linhas e aplicar filtros/ordenação no cliente.
- Exibição em tabela custom (HTML) com cabeçalho “stickied”, rolagem virtualizada (react-virtual) e largura fixa de coluna default (200px).
- Contadores: linhas filtradas vs totais visíveis localmente.

3) Filtros e Ordenação
- Linha de filtros no cabeçalho (toggle), filtro por substring (case-insensitive) aplicado client-side.
- Ordenação por coluna (toggle asc/desc) aplicada client-side na página Tabelas.
- Suporte a obtenção de valores únicos por coluna (getUniqueValues) on-demand quando abre menu da coluna (pré-carrega para futuros aprimoramentos de UX de filtro seletivo).
- Heurística: se a tabela tiver coluna requer_revisao_manual, aplica filtro automático requer_revisao_manual=true.

4) Personalização de Colunas e Linhas
- Ocultar/mostrar colunas (Dropdown “Colunas” com checkboxes).
- Estilização:
  - Por coluna: cor de texto e fundo do cabeçalho e células (Paintbrush no menu da coluna).
  - Por linha: cor de texto e fundo (menu na ação da linha).

5) Edição Local e Escrita em Parquet
- Edição inline por duplo clique na célula. Salva localmente e dispara POST /api/python/parquet/write-cell (atualiza célula por índice/coluna/valor).
- Adição de linha: atualiza local e chama POST /api/python/parquet/add-row.
- Adição de coluna: atualiza local e chama POST /api/python/parquet/add-column.
- Remoção de linha: somente local (atual), sem exclusão server-side imediata.

6) Ações e Integrações Especiais
- Exportar Excel (download direto): GET /api/python/export/excel-download?file_path=...
- Quando existe coluna codigo_original, exibe coluna fixa de “Ações de Revisão” à direita com atalhos para Agregar/Desagregar produtos por CNPJ (deduzido do caminho do arquivo).

7) Deep-Link e Estado
- Aceita /tabelas/view?file_path=... para abrir diretamente a tabela alvo.
- Guarda diretórios recentes em localStorage (sefin-audit-recent-folders) e permite abrir automaticamente um diretório pendente (sefin-audit-open-dir, setado por outras telas).


## Fluxo Client ↔ Server (Resumo)

Front-end
- listParquetFiles(dir): GET /api/python/parquet/list?directory=...
- readParquet(body): POST /api/python/parquet/read
  - Parâmetros: file_path, page, page_size, filters?, sort_column?, sort_direction?
- writeParquetCell: POST /api/python/parquet/write-cell
- addParquetRow: POST /api/python/parquet/add-row
- addParquetColumn: POST /api/python/parquet/add-column
- getUniqueValues: endpoint auxiliar em pythonApi.ts (não detalhado aqui, mas segue padrão de extração Polars)
- exportExcel: GET /api/python/export/excel-download?file_path=...

Back-end (Python/FastAPI)
- server/python/routers/parquet.py
  - /api/python/parquet/list: lista *.parquet no diretório
  - /api/python/parquet/read: lê Parquet com filtros (regex case-insensitive com Polars), ordenação, paginação (slice)
  - /api/python/parquet/write-cell: atualiza célula individual e regrava Parquet
  - /api/python/parquet/add-row: adiciona nova linha vazia e regrava Parquet
  - /api/python/parquet/add-column: adiciona coluna com valor default e regrava Parquet
- server/python/routers/export.py
  - /api/python/export/excel-download: lê Parquet e devolve Excel formatado (xlsxwriter + Arial 9, cabeçalho negrito, autoajuste)

Observações
- No endpoint /read atual, total_rows = filtered_rows (filtros já aplicados). O front Tabelas faz filtros/ordenação local quando carrega um volume grande (100k), enquanto outras páginas (ParquetViewer, Revisão Manual, Agregação por Seleção) usam filtros/ordenação server-side com paginação real.


## Decisões e Padrões de Design
- Preferência por Polars para IO e transformações (simplicidade/performance).
- Renderização custom com virtualização em vez de bibliotecas de tabela prontas. Isso dá controle fino de UX, porém exige manutenção própria.
- Edição otimista: UI atualiza primeiro e depois escreve no Parquet; não há rollback/feedback detalhado por célula em caso de erro de persistência.
- Integração com auditoria (Ações de Revisão) acoplada por convenção de coluna (codigo_original) e extração de CNPJ do path.


## Pontos Fortes
- Performance de rolagem com react-virtual mesmo com milhares de linhas.
- Editor inline simples e rápido, com adição de linhas/colunas.
- Ocultar/mostrar colunas e personalização visual agilizam análises ad hoc.
- Deep-link por file_path acelera navegação entre módulos.
- Exportação para Excel pronta e formatada.


## Limitações Identificadas
- Carregamento de 100k linhas no cliente pode onerar memória/tempo inicial; sem paginação client-side real (apenas virtualização) e sem total_rows global vindo do server quando filtrado localmente.
- Filtros/ordenação duplicam lógicas entre client e server (páginas variam a estratégia). Risco de inconsistência e complexidade de manutenção.
- Remoção de linha não persiste server-side (inconsistência com add/edit). Não há "undo" e nem controle transacional.
- Falta gerenciamento de estado/colunas (largura, ordem, estilos, visibilidade) persistente por arquivo/usuário.
- Falta seleção múltipla (checkbox por linha) e ações em lote básicas (excluir, editar campo fixo, exportar recorte).
- Falta feedback granular por célula em erros de gravação e mecanismo de retry/rollback.
- Concurrency: não há controle de lock/versão do arquivo; gravações concorrentes podem sobrescrever mudanças.
- Segurança: write endpoints aceitam paths arbitrários; dependem do ambiente controlado. Precisaria defesa extra se exposto.


## Melhorias Propostas

A) Arquitetura/Dados
- Unificar estratégia de paginação/filtragem/ordenação: adotar server-side por padrão para arquivos grandes, com paginação real e retorno de total_rows (sem filtros) e filtered_rows (pós-filtro). Atualizar a página Tabelas para usar a mesma estratégia do ParquetViewer, incluindo page/page_size e manter virtualização para experiência suave.
- Suporte a "pushdown" de filtros complexos: operadores (>, <, =, in, between, regex, nulos) por coluna e tipos corretos (numeric/date/bool). No UI, oferecer construtor simples por coluna.
- Campo total_rows sem filtros: no /read atual, total_rows e filtered_rows são iguais. Ajustar para calcular total_rows original (ex.: carga lazy + count antes de aplicar filtros) e retornar ambos corretamente.
- Adicionar endpoint de delete-row e delete-rows (por índices/condição) e garantir atomicidade (gravar temporário e mover).
- Versionamento/lock otimista: incluir um etag ou hash do arquivo no payload de escrita (write-cell/add-row/add-column/delete) e rejeitar se o arquivo mudou desde o carregamento.

B) UX/Usabilidade
- Painel de filtros avançados: 
  - Tipagem automática de colunas (mostrar operadores adequados por tipo) e chips de filtros ativos.
  - Dropdown de valores únicos com busca incremental (já existe getUniqueValues em background).
  - Botão "Aplicar" e "Limpar" com teclado Enter/Escape.
- Paginação visual: barra com página atual, tamanho da página, total filtrado vs total global. Saltos rápidos e "ir para".
- Seleção múltipla por checkbox e ações em lote (ex.: definir valor de uma coluna, excluir, exportar subconjunto).
- Colunas: 
  - Redimensionamento por arrastar, reorder por drag-and-drop, congelar (pin) à esquerda/direita.
  - Persistir preferências por arquivo (localStorage/chave por path) e opção de reset.
- Edição:
  - Validação por tipo (numérica, data) e máscara/formatador por coluna.
  - Status de gravação por célula (saving/saved/error) com retry; fila para evitar floods de I/O.
  - Edição em massa: preencher para baixo, colar múltiplas células (CSV-like) e desfazer (undo stack) local.
- Acessibilidade: navegação por teclado (setas, Enter, Esc), foco visível, descrição de colunas.
- Exportar: 
  - Exportar "visão atual" (aplicar filtros/ordenação/colunas visíveis) e não só arquivo bruto.
  - Exportar CSV além de Excel.

C) Performance
- Para arquivos muito grandes: leitura lazy (scan_parquet) e projeção de colunas (select) conforme colunas visíveis. Paginação verdadeira no back (slice) antes do materialize.
- Cache de páginas e prefetch (p+1) com react-query.
- Debounce de filtros e envio somente quando o usuário confirma/aperta Enter.
- Workers no front para ordenar/filtrar local sem travar a UI quando necessário.

D) Robustez e Segurança
- Sanitização e whitelisting de diretórios-base permitidos para leitura/escrita, evitando path traversal.
- Logs e auditoria de mudanças (quem alterou, quando, antes/depois) com arquivo .log paralelo ao .parquet ou trilha no banco.
- Testes de integração cobrindo /write-cell, /add-row, /add-column, delete e concorrência simulada.

E) Integrações de Auditoria
- Desacoplar a coluna especial "Ações de Revisão" por meio de um registry de extensões: se arquivo pertencer a um domínio (ex.: produtos) e houver coluna/metadata, injetar ações através de um provider; isso evita condicional espalhada.
- Tela de Revisão Manual e Agregação por Seleção já usam server-side; padronizar experiência e componentes para reuso (colunas, filtros, sort, badges de contagem, cabeçalho sticky, ações por linha).


## Roadmap Sugerido

Fase 1 — Padronização de Dados e UX
- Atualizar /api/python/parquet/read para retornar total_rows (sem filtros) e filtered_rows (com filtros) de forma consistente; se possível, usar scan + count antes/depois do filtro.
- Introduzir paginação server-side na página Tabelas.tsx (page/page_size 1000~5000) e mover ordenação/filtros para o back por padrão.
- Persistir preferências de coluna (visibilidade, larguras, ordem) por file_path em localStorage.

Fase 2 — Edição e Operações em Massa
- Implementar endpoints de delete-row(s) e editar em lote (por condição/seleção) com versionamento otimista.
- UI: seleção múltipla por checkbox; barra de ações em lote; status granular de gravação.

Fase 3 — Filtros Avançados e Performance
- Painel de filtros com operadores (>, <, =, in, between, is null, regex) e autodetecção de tipos.
- Projeção de colunas e prefetch de páginas; react-query para cache e invalidação previsível.

Fase 4 — Segurança e Auditoria
- Whitelist de diretórios-base, trilha de auditoria para mudanças, testes de concorrência.
- Desacoplamento das "Ações de Revisão" via provider/extensão configurável por metadata do arquivo.


## Referências de Código
- Front
  - client/src/pages/Tabelas.tsx — viewer principal com virtualização, filtros e edição inline.
  - client/src/components/ParquetViewer.tsx — abordagem com paginação server-side, filtros/ordenação persistidos; útil como base para padronização.
  - client/src/pages/RevisaoManual.tsx e client/src/pages/AgregacaoSelecao.tsx — exemplos adicionais de uso server-side.
  - client/src/lib/pythonApi.ts — contratos de ParquetReadResponse e chamadas dos endpoints Python.
- Back
  - server/python/routers/parquet.py — list/read/write-cell/add-row/add-column.
  - server/python/routers/export.py — exportação para Excel (download e por diretório).


## Conclusão
O módulo atual já oferece uma base sólida para exploração e edição rápida de Parquets, com boa performance de rolagem. As melhorias propostas visam padronizar a estratégia de dados (server-side), fortalecer a robustez das operações de escrita, elevar a UX (filtros avançados, seleção e ações em massa, preferências persistentes) e endereçar segurança e concorrência. Com a adoção incremental do roadmap, o viewer se consolida como ferramenta de análise e curadoria de dados de alta escala e confiabilidade.
