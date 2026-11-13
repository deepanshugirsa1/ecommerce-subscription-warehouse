with src as (
    select * from {{ source('raw', 'subscriptions') }}
)
select
    sub_id,
    user_id,
    plan,
    status,
    cast(mrr as double)                         as mrr,
    cast(started_at as date)                    as started_at,
    nullif(cancelled_at, '')::date              as cancelled_at,
    date_trunc('month', cast(started_at as date))        as started_month,
    date_trunc('month', nullif(cancelled_at, '')::date)  as cancelled_month
from src
