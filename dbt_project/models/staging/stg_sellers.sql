select distinct
    cast(seller_id as varchar(32)) as seller_id,
    cast(seller_zip_code_prefix as varchar(10)) as zip_code_prefix,
    cast(lower(seller_city) as varchar(100)) as city,
    cast(upper(seller_state) as varchar(2)) as state
from {{ source('olist', 'sellers') }}
where seller_id is not null