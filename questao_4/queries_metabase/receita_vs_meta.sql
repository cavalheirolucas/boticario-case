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
    printf('%d-%02d', r.ano, r.mes) AS ano_mes,
    ROUND(r.receita, 2) AS receita,
    ROUND(m.meta, 2) AS meta,
    ROUND(1.0 * r.receita / m.meta, 4) AS pct_atingimento
FROM receita_mensal r
JOIN meta_mensal m ON m.ano = r.ano AND m.mes = r.mes
ORDER BY r.ano, r.mes;