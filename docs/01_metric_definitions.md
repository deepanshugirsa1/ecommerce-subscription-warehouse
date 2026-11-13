# Metric Definitions

Governed definitions for the subscription marts. Each metric names its grain,
formula, and edge cases so downstream teams read one number the same way.

| Metric | Grain | Definition | Edge cases |
|--------|-------|------------|-----------|
| `active_subscriptions` | month | Distinct subscriptions active at any point in the month | A sub is active from `started_month` through the month **before** `cancelled_month` |
| `active_mrr` | month | Sum of plan MRR across active subscriptions | Plan price is fixed per tier (basic 9, pro 29, enterprise 99) |
| `new_mrr` | month | MRR added by subscriptions that started that month | Counts the started month only |
| `churned_mrr` | month | MRR lost by subscriptions cancelled that month | Null `cancelled_month` excluded |
| `net_new_mrr` | month | `new_mrr − churned_mrr` | Can be negative in high-churn months |
| `arpu` | month | `active_mrr / active_subscriptions` | Null-safe denominator |
| `lifetime_churn_rate` | overall | Cancelled subscriptions / total subscriptions | Bounded [0, 1] |
| `current_mrr` | snapshot | `active_mrr` of the latest month | Drives `arr = current_mrr × 12` |
| `retention_rate` | cohort × offset | Subscriptions still active N months after signup / cohort size | Bounded [0, 1] |
| `txn_success_rate` | platform | Succeeded transactions / total transactions | Null-safe denominator |

## Plan pricing

| Plan | Monthly price |
|------|---------------|
| basic | $9 |
| pro | $29 |
| enterprise | $99 |
