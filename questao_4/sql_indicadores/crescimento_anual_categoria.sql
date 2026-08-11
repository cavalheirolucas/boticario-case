WITH receita_anual_canal AS (
    SELECT
        canal,
        ano,
        SUM(receita) AS receita_total
    FROM vendas
    WHERE flag_outlier_qtd = 0 AND ano IN (2024, 2025)
    GROUP BY canal, ano
)
SELECT
    a.canal,
    ROUND(a.receita_total * 1.0 / b.receita_total - 1, 4) AS crescimento_anual
FROM receita_anual_canal a
JOIN receita_anual_canal b ON b.canal = a.canal AND b.ano = 2024
WHERE a.ano = 2025
ORDER BY crescimento_anual DESC;