-- A Type 2 chain is only trustworthy if exactly one version is in force on any
-- given day. Overlapping windows silently double-count revenue in every
-- point-in-time join, and the fact table cannot detect it. Returns a row per
-- offending version, so dbt fails the build.
with chain as (
    select
        sub_id,
        version,
        valid_from,
        valid_to,
        lead(valid_from) over (partition by sub_id order by version) as next_valid_from
    from {{ ref('dim_subscription_history') }}
)
select *
from chain
where next_valid_from is not null
  and (
        valid_to >= next_valid_from        -- overlap
     or valid_to < valid_from              -- inverted window
     or valid_to + interval 1 day <> next_valid_from   -- gap: a day with no version
  )
