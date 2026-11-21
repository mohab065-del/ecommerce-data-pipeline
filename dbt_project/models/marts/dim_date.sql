with numbers as (
    select top 1461 row_number() over (order by a.object_id) - 1 as n
    from sys.all_objects a
    cross join sys.all_objects b
),
dates as (
    select dateadd(day, n, cast('2016-01-01' as date)) as full_date
    from numbers
)
select
    convert(int, convert(char(8), full_date, 112)) as date_key,
    full_date,
    year(full_date) as year,
    datepart(quarter, full_date) as quarter,
    month(full_date) as month,
    datename(month, full_date) as month_name,
    day(full_date) as day,
    (datediff(day, '19000101', full_date) % 7) + 1 as day_of_week,
    datename(weekday, full_date) as day_name,
    datepart(iso_week, full_date) as week_of_year,
    case when (datediff(day, '19000101', full_date) % 7) + 1 in (6, 7) then 1 else 0 end as is_weekend
from dates