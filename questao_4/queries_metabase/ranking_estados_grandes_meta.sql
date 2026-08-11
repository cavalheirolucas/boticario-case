WITH receita_estado AS (
    SELECT
        estado,
        SUM(receita) AS receita
    FROM vendas
    WHERE flag_outlier_qtd = 0
    GROUP BY estado
    ORDER BY receita DESC
    LIMIT 10
),
meta_estado AS (
    SELECT
        estado,
        SUM(meta_faturamento_mensal) AS meta
    FROM metas
    GROUP BY estado
)
SELECT
    r.estado,
    ROUND(r.receita, 2) AS receita,
    ROUND(m.meta, 2) AS meta,
    ROUND(1.0 * r.receita / m.meta, 4) AS pct_atingimento,
    ROUND(m.meta - r.receita, 2) AS gap_absoluto
FROM receita_estado r
JOIN meta_estado m ON m.estado = r.estado
ORDER BY pct_atingimento DESC
LIMIT 10;
 