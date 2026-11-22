{{
    config(
        materialized = 'incremental',
        unique_key = 'txn_id',
        incremental_strategy = 'delete+insert',
    )
}}

-- Grain = one payment transaction, attributed to the plan that was in force on
-- the day it settled.
--
-- Incremental because a full refresh of every transaction ever settled costs
-- more every month and buys nothing: yesterday's charges do not change. The
-- ones that *do* change are recent, so the model reprocesses a trailing
-- window rather than only strictly new dates — a processor can restate a
-- settled charge for a few days, and `txn_date > max(txn_date)` would miss
-- every one of those corrections. delete+insert on txn_id makes the reprocess
-- idempotent instead of double-counting the window.

with txns as (

    select * from {{ ref('stg_transactions') }}

    {% if is_incremental() %}
    where txn_date >= (
        select coalesce(max(txn_date), date '1900-01-01')
             - interval {{ var('txn_restatement_window_days', 5) }} day
        from {{ this }}
    )
    {% endif %}

),

-- Point-in-time attribution: join each charge to the subscription version
-- whose validity window contains its settlement date, not to the
-- subscription's current state.
attributed as (

    select
        t.*,
        h.subscription_version_key,
        h.plan   as plan_at_txn,
        h.mrr    as mrr_at_txn
    from txns t
    left join {{ ref('dim_subscription_history') }} h
        on  h.sub_id = t.sub_id
        and t.txn_date >= h.valid_from
        and t.txn_date <= h.valid_to

)

select
    txn_id,
    sub_id,
    user_id,
    device_id,
    txn_date,
    txn_month,
    amount,
    status,
    (status = 'succeeded') as is_successful,
    subscription_version_key,
    plan_at_txn,
    mrr_at_txn
from attributed
