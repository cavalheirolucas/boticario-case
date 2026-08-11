WITH pedidos_por_cliente AS (
    SELECT
        id_cliente,
        COUNT(DISTINCT id_venda) AS n_pedidos
    FROM vendas
    WHERE flag_outlier_qtd = 0
      AND canal IN ('Ecomm mono', 'Ecomm multi')
      AND id_cliente IS NOT NULL
    GROUP BY id_cliente
)
SELECT
    ROUND(1.0 * SUM(CASE WHEN n_pedidos = 1 THEN 1 ELSE 0 END) / COUNT(*), 4) AS pct_pedido_unico
FROM pedidos_por_cliente;