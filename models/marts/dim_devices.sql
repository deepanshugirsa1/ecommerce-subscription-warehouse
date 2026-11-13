with devices as (
    select * from {{ ref('stg_devices') }}
)
select
    device_id,
    user_id,
    platform,
    registered_at
from devices
