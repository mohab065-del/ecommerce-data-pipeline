select
    c.state,
    count(distinct c.customer_key) as customers,
    count(distinct f.order_id) as orders,
    sum(f.total_usd) as revenue_usd,
    sum(f.total_usd) / nullif(count(distinct c.customer_key), 0) as revenue_per_customer_usd
from {{ ref('fct_sales') }} f
join {{ ref('dim_customer') }} c on c.customer_key = f.customer_key
where f.order_status not in ('canceled', 'unavailable')
group by c.state