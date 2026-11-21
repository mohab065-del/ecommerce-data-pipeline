{{ config(post_hook=[
    "{{ create_index(this, 'ix_fct_sales_date', ['order_date_key']) }}",
    "{{ create_index(this, 'ix_fct_sales_customer', ['customer_key']) }}",
    "{{ create_index(this, 'ix_fct_sales_product', ['product_key']) }}",
    "{{ create_index(this, 'ix_fct_sales_seller', ['seller_key']) }}",
    "{{ create_index(this, 'ix_fct_sales_status_date', ['order_status', 'order_date_key']) }}"
]) }}

with order_dates as (
    select distinct purchase_date
    from {{ ref('stg_orders') }}
    where purchase_date is not null
),
date_fx as (
    select
        d.purchase_date,
        fx.rate_date,
        fx.brl_to_usd
    from order_dates d
    outer apply (
        select top 1 r.rate_date, r.brl_to_usd
        from {{ ref('stg_fx_rates') }} r
        where r.rate_date <= d.purchase_date
        order by r.rate_date desc
    ) fx
)
select
    concat(i.order_id, '-', i.order_item_id) as sales_key,
    i.order_id,
    i.order_item_id,
    c.customer_unique_id as customer_key,
    i.product_id as product_key,
    i.seller_id as seller_key,
    convert(int, convert(char(8), o.purchase_date, 112)) as order_date_key,
    o.order_status,
    i.price as price_brl,
    i.freight_value as freight_brl,
    i.price + i.freight_value as total_brl,
    fx.brl_to_usd as fx_rate,
    fx.rate_date as fx_rate_date,
    datediff(day, fx.rate_date, o.purchase_date) as fx_gap_days,
    round(i.price * fx.brl_to_usd, 2) as price_usd,
    round(i.freight_value * fx.brl_to_usd, 2) as freight_usd,
    round((i.price + i.freight_value) * fx.brl_to_usd, 2) as total_usd
from {{ ref('stg_order_items') }} i
join {{ ref('stg_orders') }} o on o.order_id = i.order_id
left join {{ ref('stg_customers') }} c on c.customer_id = o.customer_id
left join date_fx fx on fx.purchase_date = o.purchase_date