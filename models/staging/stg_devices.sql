with src as (
    select * from {{ source('raw', 'devices') }}
)
select
    device_id,
    user_id,
    platform,
    cast(registered_at as date) as registered_at
from src
