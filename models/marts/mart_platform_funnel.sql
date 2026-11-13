-- Device-platform breakdown: registrations, paying users, and payment success.
with devices as (
    select * from {{ ref('stg_devices') }}
),
txns as (
    select * from {{ ref('fct_transactions') }}
)
select
    d.platform,
    count(distinct d.device_id)                                    as devices,
    count(distinct d.user_id)                                      as users,
    count(distinct t.txn_id)                                       as transactions,
    sum(case when t.is_successful then 1 else 0 end)               as successful_transactions,
    sum(case when not t.is_successful then 1 else 0 end)           as failed_transactions,
    round(
        sum(case when t.is_successful then 1 else 0 end)::double
        / nullif(count(t.txn_id), 0), 4
    )                                                              as txn_success_rate,
    round(sum(case when t.is_successful then t.amount else 0 end), 2) as revenue
from devices d
left join txns t on t.device_id = d.device_id
group by 1
order by revenue desc
