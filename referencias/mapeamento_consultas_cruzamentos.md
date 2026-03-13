# Mapeamento: `consultas_cruzamentos/` → Análises

Pasta dedicada às consultas SQL usadas para gerar os arquivos Parquet.
A pasta original `consultas_sql_oracle/` permanece intacta como referência.

## Consultas e suas finalidades

| Arquivo SQL | Tabela Oracle Principal | Usado por |
|---|---|---|
| `c100.sql` | `sped.reg_c100` | NFe vs EFD (C100), Ressarcimento v2, Fronteira v2 |
| `c170_simplificada.sql` | `sped.reg_c170` | Ressarcimento v2, Fronteira v2 |
| `c170_v2.sql` | `sped.reg_c170` (completo) | Fronteira v1 (legado) |
| `c176.sql` | `sped.reg_c176` | Ressarcimento v1 (legado) |
| `c176_simplificada.sql` | `sped.reg_c176` | Ressarcimento v2 |
| `reg_0200_simplificada.sql` | `sped.reg_0200` | Ressarcimento v2 (cadastro itens) |
| `nfe_simplificada.sql` | `bi.fato_nfe_detalhe` | Ressarcimento v2 (NFe itens) |
| `nfe_dados_st_simplificada.sql` | `bi.nfe_xml` (XMLTABLE) | Ressarcimento v2, Fronteira v2 (ST retido XML) |
| `nfe_entradas_interestaduais_simplificada.sql` | `bi.fato_nfe_detalhe` | Fronteira v2 (capa NFs interestadual) |
| `sitafe_calculo_simplificada.sql` | `sitafe.sitafe_nfe_calculo_item` | Ressarcimento v2, Fronteira v2 |
| `sitafe_lancamentos_simplificada.sql` | `sitafe.sitafe_nf_lancamento` + `sitafe_lancamento` | Fronteira v2 (guias/DAREs) |
| `sitafe_inferencia_sefin_simplificada.sql` | `sitafe_cest_ncm` / `sitafe_cest` / `sitafe_ncm` | Fronteira v2 (inferência 3 níveis) |
| `sitafe_mercadoria_simplificada.sql` | `sitafe.sitafe_mercadoria` + `sitafe_produto_sefin_aux` | Fronteira v2 (MVA/alíquotas) |
| `NFe.sql` | `bi.fato_nfe_detalhe` (seq_nitem=1) | NFe vs EFD (C100) — capa da nota |
| `NFe_Evento.sql` | `bi.dm_eventos` | NFe vs EFD (C100) — eventos (cancelamento, etc.) |
| `Nfe_com_nf_referenciada.sql` | `bi.dm_nfe_referenciada` | NFe vs EFD (C100) — NFe referenciadas (devoluções) |
| `dados_cadastrais.sql` | Diversas tabelas cadastrais | Relatórios gerais |

## Bind Variables (Parâmetros)

Todas as consultas usam `:CNPJ` como parâmetro obrigatório.

Opcionais:
- `:data_inicial` — data de início do período (DD/MM/YYYY)
- `:data_final` — data final do período (DD/MM/YYYY) 
- `:data_limite_processamento` — corte para retificadoras SPED
- `:codigo_item` — filtro opcional por produto
