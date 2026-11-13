-- Retention rate must stay within [0, 1].
select cohort_month, month_offset, retention_rate
from {{ ref('mart_retention_cohort') }}
where retention_rate < 0 or retention_rate > 1
