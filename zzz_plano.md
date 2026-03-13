[2026-03-07 16:11:43,431] ERROR in api: [agrupamento_produtos] Erro: 'ExprListNameSpace' object has no attribute 'lengths'

Traceback (most recent call last):

  File "C:\Users\eniot\OneDrive - SECRETARIA DE ESTADO DE FINANCAS\Desenvolvimento\sefin_audit_2\server\python\api.py", line 1579, in agrupar_produtos

    resultado = executar_agrupamento_produtos(cnpj_limpo)

                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  File "C:\Users\eniot\OneDrive - SECRETARIA DE ESTADO DE FINANCAS\Desenvolvimento\sefin_audit_2\cruzamentos\agrupamento_produtos.py", line 445, in executar_agrupamento_produtos

    discrepancias, duplicidades = _detectar_discrepancias_e_duplicidades(base_com_chave)

                                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  File "C:\Users\eniot\OneDrive - SECRETARIA DE ESTADO DE FINANCAS\Desenvolvimento\sefin_audit_2\cruzamentos\agrupamento_produtos.py", line 323, in _detectar_discrepancias_e_duplicidades

    pl.col("ncms").list.lengths().alias("qtd_ncms"),

    ^^^^^^^^^^^^^^^^^^^^^^^^^^^

AttributeError: 'ExprListNameSpace' object has no attribute 'lengths'



INFO:     127.0.0.1:55457 - "POST /api/python/produtos/agrupamento HTTP/1.1" 500 Internal Server Error

[2026-03-07 16:11:45,151] INFO in api: [agrupamento_produtos] Iniciando para CNPJ 37671507000187

🔄 Iniciando agrupamento de produtos para 37671507000187

[2026-03-07 16:11:45,189] ERROR in api: [agrupamento_produtos] Erro: 'ExprListNameSpace' object has no attribute 'lengths'

Traceback (most recent call last):

  File "C:\Users\eniot\OneDrive - SECRETARIA DE ESTADO DE FINANCAS\Desenvolvimento\sefin_audit_2\server\python\api.py", line 1579, in agrupar_produtos

    resultado = executar_agrupamento_produtos(cnpj_limpo)

                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  File "C:\Users\eniot\OneDrive - SECRETARIA DE ESTADO DE FINANCAS\Desenvolvimento\sefin_audit_2\cruzamentos\agrupamento_produtos.py", line 445, in executar_agrupamento_produtos

    discrepancias, duplicidades = _detectar_discrepancias_e_duplicidades(base_com_chave)

                                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  File "C:\Users\eniot\OneDrive - SECRETARIA DE ESTADO DE FINANCAS\Desenvolvimento\sefin_audit_2\cruzamentos\agrupamento_produtos.py", line 323, in _detectar_discrepancias_e_duplicidades

    pl.col("ncms").list.lengths().alias("qtd_ncms"),

    ^^^^^^^^^^^^^^^^^^^^^^^^^^^

AttributeError: 'ExprListNameSpace' object has no attribute 'lengths'



INFO:     127.0.0.1:55457 - "POST /api/python/produtos/agrupamento HTTP/1.1" 500 Internal Server Error

analisar projeto e verificar inconsistências, erros e bugs

fatores_conversao.py
+2
-2
    # Status de validação simplificado    fatores = fatores.with_columns(        pl.when(pl.col("flag_fator_extremo"))
    # Status de validação simplificado        pl.when(pl.col("flag_fator_extremo"))    # Status de validação simplificado (extremos ou fator nulo por ref zero/ausente)    fatores = fatores.with_columns(        pl.when(pl.col("flag_fator_extremo") | pl.col("fator").is_null())
Resumo do que foi analisado e ajustado:

Análise do projeto – correções feitas
1. cruzamentos/fatores_conversao.py
Divisão por zero: Quando preco_medio_ref era 0 (ex.: soma_total zero para a unidade de referência), o cálculo preco_medio_origem / preco_medio_ref gerava inf ou erro.
Correção: uso de pl.when(...).then(...).otherwise(pl.lit(None)) para só calcular o fator quando preco_medio_ref for não nulo e > 0; caso contrário o fator fica null.
Status de validação: Linhas com fator nulo (por ref zero/ausente) continuavam como "OK".
Correção: status_validacao passa a ser "SUSPEITO" quando flag_fator_extremo ou fator for nulo.
2. server/python/api.py – importação de fatores por Excel
Chaves duplicadas no Excel: Se o usuário enviasse duas linhas com o mesmo (chave_produto, ano_referencia, unidade_origem), o join duplicava linhas no Parquet.
Correção: aplicado .unique(subset=["chave_produto", "ano_referencia", "unidade_origem"], keep="last") no DataFrame do Excel antes do merge, mantendo uma linha por chave (última prevalecendo).
3. cruzamentos/agrupamento_produtos.py
Polars: Uso de .list.len() está correto; .list.lengths() está obsoleto e já foi substituído anteriormente. Nada a alterar aqui.
4. Frontend e API
AnaliseAgrupamentoProdutos.tsx e pythonApi.ts estão alinhados com os endpoints (agrupamento, fatores, importação de Excel). Nenhuma inconsistência encontrada que exija mudança de código.
Pendências (já conhecidas, não corrigidas nesta passagem):

Resolver em lote por nível (Discrepâncias/Duplicidades): botões ainda desabilitados; depende do backend de mapa De/Para.
Coincidências: tela/aba ainda não implementada.
Refazer movimentos (aplicar agrupamento): job que aplica o mapa aos movimentos ainda não implementado.
Se quiser, posso focar em algum desses pontos (por exemplo, endpoint de “resolver em lote” ou tela de Coincidências) ou rodar testes/lint em mais arquivos.

construir Refazer movimentos (aplicar agrupamento): job que aplica o mapa aos movimentos ainda não implementado.

Desenhar estratégia para job de refazer movimentos (aplicar agrupamento) usando dim_produto/mapas existentes
Implementar módulo Python que aplica o mapa de produtos aos movimentos (parquets de NFe/NFCe/EFD) e gera saídas ajustadas
Expor endpoint/API e, se necessário, acionar via tela (Processar Tudo)
Vou criar um módulo Python que aplica o chave_produto/código ajustado em NFe/NFCe e C170 e expor isso via um novo endpoint na API.