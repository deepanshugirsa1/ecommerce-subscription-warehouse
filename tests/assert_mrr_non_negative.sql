-- MRR aggregates must never be negative.
select month, active_mrr, new_mrr, churned_mrr
from {{ ref('mart_mrr_monthly') }}
where active_mrr < 0 or new_mrr < 0 or churned_mrr < 0
