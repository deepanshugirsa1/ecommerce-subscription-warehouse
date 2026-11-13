with txns as (
    select * from {{ ref('stg_transactions') }}
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
    (status = 'succeeded') as is_successful
from txns
