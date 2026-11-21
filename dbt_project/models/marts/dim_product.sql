{{ config(post_hook=["{{ create_index(this, 'ux_dim_product_key', ['product_key']) }}"]) }}

select
    product_id as product_key,
    coalesce(category_pt, 'unknown') as category_pt,
    coalesce(category_en, category_pt, 'unknown') as category_en,
    weight_g,
    length_cm,
    height_cm,
    width_cm
from {{ ref('stg_products') }}