select
    d.full_date,
    d.year,
    d.month,
    count(distinct f.order_id) as orders,
    count(*) as items,
    sum(f.price_usd) as revenue_usd,
    sum(f.freight_usd) as freight_usd,
    sum(f.total_usd) / nullif(count(distinct f.order_id), 0) as avg_order_value_usd
from {{ ref('fct_sales') }} f
join {{ ref('dim_date') }} d on d.date_key = f.order_date_key
where f.order_status not in ('canceled', 'unavailable')
group by d.full_date, d.year, d.month