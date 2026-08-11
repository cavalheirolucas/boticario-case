SELECT
    categoria_produto,
    ROUND(SUM(receita), 2) AS receita,
    ROUND(SUM(margem), 2) AS margem,
    ROUND(1.0 * SUM(margem) / SUM(receita), 4) AS pct_margem,
    ROUND(1.0 * SUM(receita) / (SELECT SUM(receita) FROM vendas WHERE flag_outlier_qtd = 0), 4) AS pct_receita_total
FROM vendas
WHERE flag_outlier_qtd = 0
GROUP BY categoria_produto
ORDER BY receita DESC;
 