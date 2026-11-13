-- One row per calendar month in the analysis window (2025).
with bounds as (
    select
        date_trunc('month', min(started_at)) as first_month,
        date '2025-12-01'                    as last_month
    from {{ ref('stg_subscriptions') }}
)
select
    cast(m as date) as month
from bounds,
     unnest(generate_series(first_month, last_month, interval 1 month)) as t(m)
