select distinct
    cast(customer_id as varchar(32)) as customer_id,
    cast(customer_unique_id as varchar(32)) as customer_unique_id,
    cast(customer_zip_code_prefix as varchar(10)) as zip_code_prefix,
    cast(lower(customer_city) as varchar(100)) as city,
    cast(upper(customer_state) as varchar(2)) as state
from {{ source('olist', 'customers') }}
where customer_id is not null