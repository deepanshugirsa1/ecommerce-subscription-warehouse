with src as (
    select * from {{ source('raw', 'subscription_events') }}
)
select
    event_id,
    sub_id,
    user_id,
    event_type,
    plan                                          as plan_after_event,
    cast(event_date as date)                      as event_date,
    date_trunc('month', cast(event_date as date)) as event_month,
    cast(mrr_change as double)                    as mrr_change
from src
