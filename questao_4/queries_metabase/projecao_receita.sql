WITH receita_anual AS (
    SELECT
        ano,
        SUM(receita) AS receita_total
    FROM vendas
    WHERE flag_outlier_qtd = 0 AND ano IN (2024, 2025)
    GROUP BY ano
),
crescimento AS (
    SELECT
        (SELECT receita_total FROM receita_anual WHERE ano = 2025) * 1.0
        / (SELECT receita_total FROM receita_anual WHERE ano = 2024) - 1 AS taxa
),
media_sazonal AS (
    SELECT
        mes,
        AVG(receita_mes) AS media_historica
    FROM (
        SELECT
            ano,
            mes,
            SUM(receita) AS receita_mes
        FROM vendas
        WHERE flag_outlier_qtd = 0 AND ano IN (2024, 2025)
        GROUP BY ano, mes
    )
    GROUP BY mes
),
historico AS (
    SELECT
        ano || '-' || substr('00' || mes, -2, 2) AS periodo,
        SUM(receita) AS receita_realizada,
        NULL AS receita_projetada
    FROM vendas
    WHERE flag_outlier_qtd = 0
    GROUP BY ano, mes
),
projecao AS (
    SELECT
        '2026-' || substr('00' || ms.mes, -2, 2) AS periodo,
        NULL AS receita_realizada,
        ROUND(ms.media_historica * (1 + c.taxa), 2) AS receita_projetada
    FROM media_sazonal ms
    CROSS JOIN crescimento c
    WHERE ms.mes IN (7, 8, 9, 10, 11, 12)
),
ponte AS (
    SELECT
        periodo,
        receita_realizada,
        receita_realizada AS receita_projetada
    FROM historico
    WHERE periodo = (SELECT MAX(periodo) FROM historico)
)
SELECT * FROM historico WHERE periodo != (SELECT MAX(periodo) FROM historico)
UNION ALL
SELECT * FROM ponte
UNION ALL
SELECT * FROM projecao
ORDER BY periodo;