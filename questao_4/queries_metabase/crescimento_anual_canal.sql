WITH receita_anual_cat AS (
    SELECT
        categoria_produto,
        ano,
        SUM(receita) AS receita_total
    FROM vendas
    WHERE flag_outlier_qtd = 0 AND ano IN (2024, 2025)
    GROUP BY categoria_produto, ano
)
SELECT
    a.categoria_produto,
    ROUND(a.receita_total * 1.0 / b.receita_total - 1, 4) AS crescimento_anual
FROM receita_anual_cat a
JOIN receita_anual_cat b ON b.categoria_produto = a.categoria_produto AND b.ano = 2024
WHERE a.ano = 2025
ORDER BY crescimento_anual DESC;