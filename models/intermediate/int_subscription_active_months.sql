-- Expand each subscription into one row per month it was active, carrying MRR.
-- A subscription is active from its started_month through the month before it
-- cancelled (or through the last month in the window if still active).
with subs as (
    select * from {{ ref('stg_subscriptions') }}
),
spine as (
    select * from {{ ref('int_month_spine') }}
)
select
    s.sub_id,
    s.user_id,
    s.plan,
    s.mrr,
    sp.month,
    s.started_month,
    s.cancelled_month,
    (sp.month = s.started_month)                                   as is_new_month,
    (s.cancelled_month is not null and sp.month = s.cancelled_month) as is_churn_month
from subs s
join spine sp
  on sp.month >= s.started_month
 and (s.cancelled_month is null or sp.month < s.cancelled_month)
