WITH
    PARAMETROS AS (
        SELECT
            :CNPJ AS cnpj_filtro,
            NVL(TO_DATE(:data_inicial, 'DD/MM/YYYY'), TO_DATE('01/01/1900', 'DD/MM/YYYY')) AS dt_ini_filtro,
            NVL(TO_DATE(:data_final, 'DD/MM/YYYY'), TRUNC(SYSDATE)) AS dt_fim_filtro,
            NVL(TO_DATE(:data_limite_processamento, 'DD/MM/YYYY'), TRUNC(SYSDATE)) AS dt_corte
        FROM dual
    ),
    
    ARQUIVOS_RANKING AS (
        /* Garante apenas a última versão válida do arquivo para o período */
        SELECT
            reg_0000.id AS reg_0000_id,
            reg_0000.cnpj,
            reg_0000.cod_fin AS cod_fin_efd,
            reg_0000.dt_ini,
            reg_0000.data_entrega,
            ROW_NUMBER() OVER (
                PARTITION BY reg_0000.cnpj, reg_0000.dt_ini
                ORDER BY reg_0000.data_entrega DESC, reg_0000.id DESC
            ) AS rn
        FROM sped.reg_0000 reg_0000
        JOIN PARAMETROS p ON reg_0000.cnpj = p.cnpj_filtro
        WHERE
            reg_0000.data_entrega <= p.dt_corte
            AND reg_0000.dt_ini BETWEEN p.dt_ini_filtro AND p.dt_fim_filtro
    ),

    -------------------------------------------------------------------------
    -- 1. RESUMO DOS VALORES DE RESSARCIMENTO (BLOCOS C100/C170/C176)
    -------------------------------------------------------------------------
    RESUMO_RESSARCIMENTO AS (
        SELECT
            arq.cnpj,
            TRUNC(arq.dt_ini, 'MM') AS mes_referencia,
            -- INCLUSÃO: Contagem dos registros C176 (itens analisados para ressarcimento)
            COUNT(c176.id) AS qtd_itens_analisados,
            SUM(NVL(c170.qtd, 0) * NVL(c176.vl_unit_icms_ult_e, 0)) AS vl_ressarc_credito_proprio,
            SUM(NVL(c170.qtd, 0) * NVL(c176.vl_unit_res, 0)) AS vl_ressarc_st_retido
        FROM sped.reg_c176 c176
        INNER JOIN ARQUIVOS_RANKING arq ON c176.reg_0000_id = arq.reg_0000_id
        INNER JOIN sped.reg_c100 c100 ON c176.reg_c100_id = c100.id
        INNER JOIN sped.reg_c170 c170 ON c176.reg_c170_id = c170.id
        WHERE arq.rn = 1
        GROUP BY arq.cnpj, TRUNC(arq.dt_ini, 'MM')
    ),

    -------------------------------------------------------------------------
    -- 2. RESUMO DOS VALORES DE AJUSTE (BLOCO E111)
    -------------------------------------------------------------------------
    RESUMO_E111 AS (
        SELECT
            arq.cnpj,
            TRUNC(arq.dt_ini, 'MM') AS mes_referencia,
            -- Soma condicional para Códigos de Ajuste referentes a Crédito Próprio
            SUM(
                CASE 
                    WHEN e111.cod_aj_apur IN ('RO020023', 'RO020049') THEN e111.vl_aj_apur 
                    ELSE 0 
                END
            ) AS vl_ajuste_credito_proprio,
            -- Soma condicional para Códigos de Ajuste referentes a ST Retido
            SUM(
                CASE 
                    WHEN e111.cod_aj_apur IN ('RO020022', 'RO020047') THEN e111.vl_aj_apur 
                    ELSE 0 
                END
            ) AS vl_ajuste_st_retido,
            -- Soma individual para outros Códigos de Ajuste solicitados (Exibição apenas)
            SUM(
                CASE 
                    WHEN e111.cod_aj_apur = 'RO020050' THEN e111.vl_aj_apur 
                    ELSE 0 
                END
            ) AS vl_ajuste_ro020050,
            SUM(
                CASE 
                    WHEN e111.cod_aj_apur = 'RO020048' THEN e111.vl_aj_apur 
                    ELSE 0 
                END
            ) AS vl_ajuste_ro020048
        FROM ARQUIVOS_RANKING arq
        INNER JOIN sped.reg_e111 e111 ON e111.reg_0000_id = arq.reg_0000_id
        WHERE arq.rn = 1
        GROUP BY arq.cnpj, TRUNC(arq.dt_ini, 'MM')
    )

-------------------------------------------------------------------------
-- 3. CRUZAMENTO FINAL E CÁLCULO DAS DIFERENÇAS
-------------------------------------------------------------------------
SELECT
    COALESCE(res.cnpj, e.cnpj) AS cnpj,
    TO_CHAR(COALESCE(res.mes_referencia, e.mes_referencia), 'MM/YYYY') AS periodo_efd,
    
    -- INCLUSÃO: Apresentando a quantidade de itens analisados que embasam o cálculo
    NVL(res.qtd_itens_analisados, 0) AS qtd_itens_analisados_c176,

    -- COMPARATIVO: CRÉDITO PRÓPRIO
    NVL(res.vl_ressarc_credito_proprio, 0) AS total_ressarc_credito_proprio,
    NVL(e.vl_ajuste_credito_proprio, 0) AS total_ajuste_credito_proprio_e111,
    (NVL(res.vl_ressarc_credito_proprio, 0) - NVL(e.vl_ajuste_credito_proprio, 0)) AS diferenca_credito_proprio,

    -- COMPARATIVO: ST RETIDO
    NVL(res.vl_ressarc_st_retido, 0) AS total_ressarc_st_retido,
    NVL(e.vl_ajuste_st_retido, 0) AS total_ajuste_st_retido_e111,
    (NVL(res.vl_ressarc_st_retido, 0) - NVL(e.vl_ajuste_st_retido, 0)) AS diferenca_st_retido,

    -- OUTROS CÓDIGOS DE AJUSTE (APENAS EXIBIÇÃO)
    NVL(e.vl_ajuste_ro020050, 0) AS total_ajuste_ro020050_e111,
    NVL(e.vl_ajuste_ro020048, 0) AS total_ajuste_ro020048_e111

FROM RESUMO_RESSARCIMENTO res
FULL OUTER JOIN RESUMO_E111 e 
    ON res.cnpj = e.cnpj 
    AND res.mes_referencia = e.mes_referencia
ORDER BY 
    COALESCE(res.mes_referencia, e.mes_referencia) ASC;