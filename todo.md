# Project TODO

## Layout e Navegação
- [x] Design system (cores, tipografia, tema)
- [x] DashboardLayout customizado com sidebar e navegação por módulos
- [x] Barra de contexto com CNPJ ativo

## Módulo de Extração Oracle
- [x] Página de configuração de conexão Oracle
- [x] Página de extração de dados por CNPJ
- [x] Seleção de consultas SQL para execução
- [x] Seleção de pasta de destino para Parquet
- [x] Extração de tabelas auxiliares (sem filtro CNPJ)
- [x] Barra de progresso da extração
- [x] Backend Python API para conexão Oracle
- [x] Backend Python API para execução de consultas e salvamento Parquet

## Módulo de Visualização de Tabelas
- [x] Leitura de arquivos Parquet
- [x] Tabela interativa com filtros em todas as colunas
- [x] Edição de dados por célula (inline editing)
- [x] Inserção de novas linhas
- [x] Criação de novas colunas
- [x] Personalização de cores (letras, linhas, colunas)
- [x] Backend Python API para leitura/escrita Parquet

## Módulo de Exportação
- [x] Exportação para Excel (.xlsx)
- [x] Geração de relatórios Word (modelo Papel_TIMBRADO_SEFIN)
- [x] Geração de relatórios TXT (modelo notificacao_det)
- [x] Backend Python API para exportação

## Módulo de Análises (Expansível)
- [x] Estrutura de módulo expansível para análises futuras
- [x] Placeholder para cruzamento de tabelas
- [x] Placeholder para geração de novas tabelas via funções Python

## Infraestrutura
- [x] Testes vitest para rotas do servidor (12 testes passando)
- [x] Documentação do projeto
