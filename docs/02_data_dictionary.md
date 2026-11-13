# Data Dictionary

## Raw / staging sources

### users
| Column | Type | Description |
|--------|------|-------------|
| user_id | string | Primary key |
| signup_date | date | Account creation date |
| country | string | ISO-ish country code |
| acquisition_channel | string | organic, paid_search, referral, email, social |

### subscriptions
| Column | Type | Description |
|--------|------|-------------|
| sub_id | string | Primary key |
| user_id | string | FK -> users |
| plan | string | basic, pro, enterprise |
| status | string | active, cancelled |
| mrr | double | Monthly recurring revenue for the current plan |
| started_at | date | Subscription start |
| cancelled_at | date | Cancellation date (null if active) |

### subscription_events
| Column | Type | Description |
|--------|------|-------------|
| event_id | string | Primary key |
| sub_id | string | FK -> subscriptions |
| event_type | string | created, upgraded, downgraded, cancelled, reactivated |
| event_date | date | Event date |
| mrr_change | double | Signed MRR delta from the event |

### transactions
| Column | Type | Description |
|--------|------|-------------|
| txn_id | string | Primary key |
| sub_id | string | FK -> subscriptions |
| user_id | string | FK -> users |
| device_id | string | FK -> devices |
| amount | double | Charge amount |
| txn_date | date | Charge date |
| status | string | succeeded, failed |

### devices
| Column | Type | Description |
|--------|------|-------------|
| device_id | string | Primary key |
| user_id | string | FK -> users |
| platform | string | ios, android, web |
| registered_at | date | Registration date |

## Marts

| Model | Grain | Purpose |
|-------|-------|---------|
| `dim_users` | user | User + current subscription attributes |
| `dim_subscriptions` | subscription | Lifecycle, status, tenure |
| `dim_devices` | device | Device registrations |
| `fct_transactions` | transaction | Payment facts with success flag |
| `fct_subscription_events` | event | Lifecycle event stream |
| `mart_mrr_monthly` | month | MRR movement (active/new/churned/net, ARPU) |
| `mart_subscription_kpis` | snapshot | Single-row executive KPIs |
| `mart_retention_cohort` | cohort × offset | Cohort retention curve |
| `mart_platform_funnel` | platform | Device + payment-success breakdown |
