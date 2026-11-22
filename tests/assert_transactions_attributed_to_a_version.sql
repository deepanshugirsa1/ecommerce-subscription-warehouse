-- Every charge must land inside some subscription version's validity window.
-- An unattributed charge means the SCD2 chain starts after the charge settled,
-- which would make plan-level revenue wrong rather than merely incomplete.
select txn_id, sub_id, txn_date
from {{ ref('fct_transactions') }}
where subscription_version_key is null
