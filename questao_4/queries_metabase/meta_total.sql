WITH receita_mensal AS (
    SELECT
        ano,
        mes,
        SUM(receita) AS receita
    FROM vendas
    WHERE flag_outlier_qtd = 0
    GROUP BY ano, mes
),
meta_mensal AS (
    SELECT
        ano,
        mes,
        SUM(meta_faturamento_mensal) AS meta
    FROM metas
    GROUP BY ano, mes
)
SELECT
    ROUND(SUM(meta), 2) AS meta_total
FROM meta_mensal m;