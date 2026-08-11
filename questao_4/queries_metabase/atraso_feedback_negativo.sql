with feedback_negativo as (

	select 
	*,
	CASE WHEN  feedback_cliente in ("Suporte não responde.", "A entrega atrasou muito.", "O produto veio quebrado.") then TRUE else FALSE end as flag_feedback_negativo
	from vendas

)

SELECT
    status_entrega,
    COUNT(*) AS pedidos,
    SUM(flag_feedback_negativo) AS feedbacks_negativos,
    ROUND(1.0 * SUM(flag_feedback_negativo) / COUNT(*), 4) AS pct_feedback_negativo
FROM feedback_negativo
WHERE flag_outlier_qtd = 0
  AND canal IN ('Ecomm mono', 'Ecomm multi')
  AND status_entrega IS NOT NULL
GROUP BY status_entrega;