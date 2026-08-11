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
    r.ano || '-' || r.mes AS periodo,
    ROUND(1.0 * r.receita / m.meta, 4) AS atingimento
FROM receita_mensal r
JOIN meta_mensal m ON m.ano = r.ano AND m.mes = r.mes
ORDER BY atingimento DESC
LIMIT 1;