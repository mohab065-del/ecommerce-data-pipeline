{{ config(post_hook=["{{ create_index(this, 'ux_dim_customer_key', ['customer_key']) }}"]) }}

with latest as (
    select customer_unique_id, zip_code_prefix, city, state
    from (
        select
            c.customer_unique_id,
            c.zip_code_prefix,
            c.city,
            c.state,
            row_number() over (
                partition by c.customer_unique_id
                order by o.purchased_at desc
            ) as rn
        from {{ ref('stg_customers') }} c
        left join {{ ref('stg_orders') }} o on o.customer_id = c.customer_id
    ) x
    where rn = 1
),
agg as (
    select
        c.customer_unique_id,
        min(o.purchased_at) as first_order_at,
        max(o.purchased_at) as last_order_at,
        count(distinct o.order_id) as orders_count
    from {{ ref('stg_customers') }} c
    left join {{ ref('stg_orders') }} o on o.customer_id = c.customer_id
    group by c.customer_unique_id
)
select
    l.customer_unique_id as customer_key,
    l.zip_code_prefix,
    l.city,
    l.state,
    a.first_order_at,
    a.last_order_at,
    a.orders_count
from latest l
join agg a on a.customer_unique_id = l.customer_unique_id