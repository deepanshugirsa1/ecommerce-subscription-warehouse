with src as (
    select * from {{ source('raw', 'transactions') }}
)
select
    txn_id,
    sub_id,
    user_id,
    device_id,
    cast(amount as double)                      as amount,
    cast(txn_date as date)                      as txn_date,
    date_trunc('month', cast(txn_date as date)) as txn_month,
    status
from src
