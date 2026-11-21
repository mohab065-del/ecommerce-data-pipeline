with ranked as (
    select
        cast(order_id as varchar(32)) as order_id,
        try_cast(order_item_id as int) as order_item_id,
        cast(product_id as varchar(32)) as product_id,
        cast(seller_id as varchar(32)) as seller_id,
        coalesce(try_cast(price as decimal(12, 2)), 0) as price,
        coalesce(try_cast(freight_value as decimal(12, 2)), 0) as freight_value,
        row_number() over (
            partition by order_id, order_item_id
            order by (select null)
        ) as rn
    from {{ source('olist', 'order_items') }}
)
select order_id, order_item_id, product_id, seller_id, price, freight_value
from ranked
where rn = 1