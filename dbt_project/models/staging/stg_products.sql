with ranked as (
    select
        cast(p.product_id as varchar(32)) as product_id,
        cast(p.product_category_name as varchar(100)) as category_pt,
        cast(t.product_category_name_english as varchar(100)) as category_en,
        try_cast(p.product_weight_g as decimal(12, 2)) as weight_g,
        try_cast(p.product_length_cm as decimal(12, 2)) as length_cm,
        try_cast(p.product_height_cm as decimal(12, 2)) as height_cm,
        try_cast(p.product_width_cm as decimal(12, 2)) as width_cm,
        row_number() over (partition by p.product_id order by (select null)) as rn
    from {{ source('olist', 'products') }} p
    left join {{ source('olist', 'category_translation') }} t
        on p.product_category_name = t.product_category_name
)
select product_id, category_pt, category_en, weight_g, length_cm, height_cm, width_cm
from ranked
where rn = 1