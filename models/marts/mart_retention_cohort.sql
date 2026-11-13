-- Cohort retention: for each signup-month cohort, the share of subscriptions
-- still active N months after signup.
with active_months as (
    select * from {{ ref('int_subscription_active_months') }}
),
cohort_size as (
    select started_month as cohort_month,
           count(distinct sub_id) as cohort_subscriptions
    from active_months
    group by 1
),
retained as (
    select
        started_month                               as cohort_month,
        date_diff('month', started_month, month)    as month_offset,
        count(distinct sub_id)                      as retained_subscriptions
    from active_months
    group by 1, 2
)
select
    r.cohort_month,
    r.month_offset,
    cs.cohort_subscriptions,
    r.retained_subscriptions,
    round(r.retained_subscriptions::double / nullif(cs.cohort_subscriptions, 0), 4)
        as retention_rate
from retained r
join cohort_size cs on cs.cohort_month = r.cohort_month
order by r.cohort_month, r.month_offset
