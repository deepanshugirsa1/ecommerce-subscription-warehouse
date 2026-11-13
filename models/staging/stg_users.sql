with src as (
    select * from {{ source('raw', 'users') }}
)
select
    user_id,
    cast(signup_date as date)        as signup_date,
    date_trunc('month', cast(signup_date as date)) as signup_month,
    country,
    acquisition_channel
from src
