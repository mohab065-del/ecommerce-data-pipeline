select
    cast(order_id as varchar(32)) as order_id,
    cast(customer_id as varchar(32)) as customer_id,
    cast(lower(order_status) as varchar(20)) as order_status,
    try_cast(order_purchase_timestamp as datetime2) as purchased_at,
    try_cast(order_purchase_timestamp as date) as purchase_date
from {{ source('olist', 'orders') }}
where order_id is not null