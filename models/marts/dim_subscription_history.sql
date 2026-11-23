{{
    config(
        materialized = 'incremental',
        unique_key = 'sub_id',
        incremental_strategy = 'delete+insert',
    )
}}

-- Slowly changing dimension, Type 2: one row per subscription *version*.
--
-- dim_subscriptions answers "what plan is this subscription on now". It cannot
-- answer "what plan was this subscription on when that charge settled", which
-- is the question every revenue and unit-economics model actually asks. When a
-- subscription upgrades from basic to pro in June, a Type 1 dimension rewrites
-- history: January's $9 charge gets attributed to the pro plan and the mart
-- quietly overstates pro revenue. This model keeps every version alive with its
-- own validity window so facts can be joined as of their own event date.
--
-- unique_key is sub_id, not the surrogate key, on purpose. A Type 2 chain
-- cannot be appended to: a new event has to close the version that was open
-- before it, so the whole chain for a touched subscription is deleted and
-- rebuilt. Restating one subscription is cheap; getting its validity windows
-- wrong is not.

with events as (

    select
        sub_id,
        user_id,
        event_id,
        event_type,
        event_date,
        plan_after_event,
        mrr_change
    from {{ ref('stg_subscription_events') }}

    {% if is_incremental() %}
    -- Rebuild every subscription that has moved inside the lookback window,
    -- not just the rows that are new. The window absorbs late-arriving events:
    -- a cancellation backdated to last week still reopens its own chain.
    where sub_id in (
        select distinct e.sub_id
        from {{ ref('stg_subscription_events') }} e
        cross join (
            -- opened_at, not valid_from: version 1 is anchored at 1900 and
            -- would pin the watermark to the start of time.
            select coalesce(max(opened_at), date '1900-01-01') as watermark
            from {{ this }}
        ) w
        where e.event_date >= w.watermark - interval {{ var('scd2_lookback_days', 7) }} day
    )
    {% endif %}

),

ordered as (

    select
        *,
        row_number() over (
            partition by sub_id order by event_date, event_id
        ) as version,
        lead(event_date) over (
            partition by sub_id order by event_date, event_id
        ) as superseded_at,
        sum(mrr_change) over (
            partition by sub_id order by event_date, event_id
            rows between unbounded preceding and current row
        ) as mrr
    from events

)

select
    sub_id || '-v' || lpad(cast(version as varchar), 3, '0') as subscription_version_key,
    sub_id,
    user_id,
    version,
    event_id                as opened_by_event_id,
    event_type              as opened_by_event_type,
    plan_after_event        as plan,
    round(mrr, 2)           as mrr,
    case
        when event_type = 'cancelled' then 'cancelled'
        else 'active'
    end                     as status,
    event_date              as opened_at,
    -- The first version of a chain is open-ended at the start. A subscription
    -- created on the 15th is billed for that whole month, so its first charge
    -- settles on the 1st — before its own creation event. Anchoring version 1
    -- at its event date leaves those charges unattributable, which is the
    -- classic SCD2 off-by-one: facts fall outside the chain and plan-level
    -- revenue comes up short without any test failing. `opened_at` keeps the
    -- true event date; `valid_from` is the window the facts join against.
    case when version = 1 then date '1900-01-01' else event_date end as valid_from,
    -- Day-grain windows are closed, not half-open: valid_to is the last day the
    -- version was in force, so a point-in-time join reads
    -- `txn_date between valid_from and valid_to` with no off-by-one.
    coalesce(superseded_at - interval 1 day, date '9999-12-31') as valid_to,
    superseded_at is null   as is_current,
    date_trunc('month', event_date) as opened_at_month
from ordered
