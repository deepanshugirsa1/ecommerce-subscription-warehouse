with events as (
    select * from {{ ref('stg_subscription_events') }}
)
select
    event_id,
    sub_id,
    user_id,
    event_type,
    event_date,
    event_month,
    mrr_change
from events
