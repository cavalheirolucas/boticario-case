SELECT
    status_entrega,
    COUNT(*) AS pedidos,
    ROUND(1.0 * COUNT(*) / (
        SELECT COUNT(*)
        FROM vendas
        WHERE flag_outlier_qtd = 0
          AND canal IN ('Ecomm mono', 'Ecomm multi')
          AND status_entrega IS NOT NULL
    ), 2) AS pct_do_total
FROM vendas
WHERE flag_outlier_qtd = 0
  AND canal IN ('Ecomm mono', 'Ecomm multi')
  AND status_entrega IS NOT NULL
GROUP BY status_entrega;