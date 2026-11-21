{{ config(post_hook=["{{ create_index(this, 'ux_dim_seller_key', ['seller_key']) }}"]) }}

select
    seller_id as seller_key,
    zip_code_prefix,
    city,
    state
from {{ ref('stg_sellers') }}