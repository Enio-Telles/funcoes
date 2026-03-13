-- Tabela CEST - 2º nível
SELECT  A.IT_NU_CEST AS CEST,
        A.IT_CO_SEFIN AS "CO-SEFIN"
FROM    SITAFE.SITAFE_CEST A
WHERE   IT_IN_STATUS <> 'C'
ORDER BY  A.IT_NU_CEST;
Sign in to enable AI completions, or disable inline completions in Settings (DBCode > A