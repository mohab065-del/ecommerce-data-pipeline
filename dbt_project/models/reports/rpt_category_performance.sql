select
    p.category_en,
    count(*) as items_sold,
    count(distinct f.order_id) as orders,
    sum(f.price_usd) as revenue_usd,
    avg(f.price_usd) as avg_item_price_usd
from {{ ref('fct_sales') }} f
join {{ ref('dim_product') }} p on p.product_key = f.product_key
where f.order_status not in ('canceled', 'unavailable')
group by p.category_en