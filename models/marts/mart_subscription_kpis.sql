-- Single-row executive snapshot of the subscription business.
with subs as (
    select * from {{ ref('stg_subscriptions') }}
),
latest as (
    select active_mrr, active_subscriptions, arpu
    from {{ ref('mart_mrr_monthly') }}
    order by month desc
    limit 1
)
select
    (select count(*) from subs)                                   as total_subscriptions,
    (select count(*) from subs where status = 'active')           as active_subscriptions,
    (select count(*) from subs where status = 'cancelled')        as cancelled_subscriptions,
    round(
        (select count(*) from subs where status = 'cancelled')::double
        / nullif((select count(*) from subs), 0), 4
    )                                                             as lifetime_churn_rate,
    round((select active_mrr from latest), 2)                     as current_mrr,
    round((select active_mrr from latest) * 12, 2)                as arr,
    round((select arpu from latest), 2)                           as current_arpu
