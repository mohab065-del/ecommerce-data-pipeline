{{ config(
    materialized='table',
    as_columnstore=false,
    post_hook=["{{ create_index(this, 'ix_stg_fx_rates_date', ['rate_date']) }}"]
) }}

with ranked as (
    select
        try_cast([date] as date) as rate_date,
        try_cast([rate] as decimal(18, 8)) as brl_to_usd,
        row_number() over (
            partition by try_cast([date] as date)
            order by (select null)
        ) as rn
    from {{ source('olist', 'brl_usd_rates') }}
)
select rate_date, brl_to_usd
from ranked
where rn = 1 and rate_date is not null and brl_to_usd > 0