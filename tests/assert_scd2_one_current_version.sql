-- Every subscription has exactly one open version. Zero means the chain was
-- closed by a restatement that never reopened it; two means an incremental run
-- appended instead of rebuilding the chain, which is the failure mode this
-- model's unique_key is chosen to prevent.
select sub_id, count(*) as current_versions
from {{ ref('dim_subscription_history') }}
where is_current
group by sub_id
having count(*) <> 1
