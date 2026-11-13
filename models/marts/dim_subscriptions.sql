with subs as (
    select * from {{ ref('stg_subscriptions') }}
)
select
    sub_id,
    user_id,
    plan,
    status,
    mrr,
    started_at,
    cancelled_at,
    started_month,
    cancelled_month,
    case
        when cancelled_at is null
            then date_diff('month', started_at, date '2025-12-01')
        else date_diff('month', started_at, cancelled_at)
    end as tenure_months
from subs
