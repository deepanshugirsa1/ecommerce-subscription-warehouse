with users as (
    select * from {{ ref('stg_users') }}
),
subs as (
    select * from {{ ref('stg_subscriptions') }}
)
select
    u.user_id,
    u.signup_date,
    u.signup_month,
    u.country,
    u.acquisition_channel,
    s.sub_id,
    s.plan,
    s.status,
    s.mrr,
    s.started_at,
    s.cancelled_at
from users u
left join subs s on s.user_id = u.user_id
