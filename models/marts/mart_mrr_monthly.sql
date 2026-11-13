-- Monthly recurring revenue movement: active, new, and churned MRR per month.
with spine as (
    select * from {{ ref('int_month_spine') }}
),
active as (
    select
        month,
        count(distinct sub_id) as active_subscriptions,
        sum(mrr)               as active_mrr
    from {{ ref('int_subscription_active_months') }}
    group by 1
),
new_subs as (
    select started_month as month,
           count(*)       as new_subscriptions,
           sum(mrr)       as new_mrr
    from {{ ref('stg_subscriptions') }}
    group by 1
),
churned as (
    select cancelled_month as month,
           count(*)         as churned_subscriptions,
           sum(mrr)         as churned_mrr
    from {{ ref('stg_subscriptions') }}
    where cancelled_month is not null
    group by 1
)
select
    s.month,
    coalesce(a.active_subscriptions, 0)   as active_subscriptions,
    round(coalesce(a.active_mrr, 0), 2)   as active_mrr,
    coalesce(n.new_subscriptions, 0)      as new_subscriptions,
    round(coalesce(n.new_mrr, 0), 2)      as new_mrr,
    coalesce(c.churned_subscriptions, 0)  as churned_subscriptions,
    round(coalesce(c.churned_mrr, 0), 2)  as churned_mrr,
    round(coalesce(n.new_mrr, 0) - coalesce(c.churned_mrr, 0), 2) as net_new_mrr,
    round(
        coalesce(a.active_mrr, 0) / nullif(a.active_subscriptions, 0), 2
    ) as arpu
from spine s
left join active   a on a.month = s.month
left join new_subs n on n.month = s.month
left join churned  c on c.month = s.month
order by s.month
