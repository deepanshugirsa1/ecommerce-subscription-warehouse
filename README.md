# Subscription & Transaction Analytics Warehouse

End-to-end analytics warehouse for a **subscription business**: it generates a
realistic subscription dataset, lands it in a local lakehouse, models it into a
governed star schema with dbt, and publishes **MRR, churn, ARPU, ARR, cohort
retention, and platform-funnel** marts behind data-quality gates, a freshness
SLA, an Airflow DAG, and a Streamlit dashboard.

> **Status: Complete (local portfolio).** `generate → ingest → dbt build (+tests) → quality gates`
> run locally with CI. Production wiring (Glue/EMR, Redshift/Iceberg, Kinesis
> streaming) is documented as future scope in [docs/ROADMAP.md](docs/ROADMAP.md).

## Architecture

```
raw CSVs (users, subscriptions, events, transactions, devices)
        │   data/generate_data.py
        ▼
Spark-style ingest ──► Parquet lake (data/curated/) + DuckDB raw_* tables
        │   spark/ingest_subscriptions.py
        ▼
dbt medallion:  staging (views) ─► intermediate (views) ─► marts (tables)
        │
        ├─ dim_users / dim_subscriptions / dim_devices
        ├─ dim_subscription_history  (SCD Type 2, incremental)
        ├─ fct_transactions (incremental) / fct_subscription_events
        ├─ mart_mrr_monthly · mart_subscription_kpis
        ├─ mart_retention_cohort · mart_platform_funnel
        │
        ▼
quality gates + freshness SLA  ──►  artifacts/quality_report.json
        │   quality/run_checks.py
        ▼
Streamlit dashboard (app/dashboard.py)   ·   Airflow DAG (airflow/dags/)
```

## Quickstart

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate   |   macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

python run_demo.py                      # generate -> ingest -> dbt build -> quality gates
streamlit run app/dashboard.py          # self-service dashboard
```

## Latest local run

- **600** subscriptions (**354** active), lifetime churn **41%**
- **Current MRR $12,206** · **ARR $146,472** · **ARPU $34.48**
- dbt: **70 passed** (10 models, 53 tests, 7 views) · quality gates **14/14 HEALTHY** · freshness **PASS**

See [docs/01_metric_definitions.md](docs/01_metric_definitions.md) and
[docs/02_data_dictionary.md](docs/02_data_dictionary.md).

## Type 2 history and incremental loads

`dim_subscriptions` answers *what plan is this subscription on now*. It cannot
answer *what plan was it on when that charge settled* — and that is the
question every revenue and unit-economics model actually asks. When a
subscription upgrades from basic to pro in June, a Type 1 dimension rewrites
history: January's $9 charge is attributed to pro, and plan-level revenue is
overstated with nothing failing.

`dim_subscription_history` keeps every version alive with its own validity
window:

| subscription_version_key | plan | mrr | opened_at | valid_from | valid_to | is_current |
|---|---|---|---|---|---|---|
| s0042-v001 | basic | 9.00 | 2025-02-15 | 1900-01-01 | 2025-06-30 | false |
| s0042-v002 | pro | 29.00 | 2025-07-01 | 2025-07-01 | 9999-12-31 | true |

`fct_transactions` then joins on `txn_date between valid_from and valid_to`, so
each charge carries the plan and MRR in force on its own settlement date.

Two details that are easy to get wrong, and are the reason the singular tests
exist:

- **Windows are closed, and version 1 is open-ended at the start.** A
  subscription created on the 15th is billed for the whole month, so its first
  charge settles on the 1st — *before* its own creation event. Anchoring
  version 1 at its event date leaves those charges unattributable and
  plan-level revenue short, with no test failing. `opened_at` keeps the true
  event date; `valid_from` is the window facts join against.
- **A Type 2 chain cannot be appended to.** A new event has to close the
  version that was open before it, so the incremental run deletes and rebuilds
  the whole chain for any subscription that moved inside the lookback window
  (`unique_key = 'sub_id'`, not the surrogate key).

Both incremental models reach backwards rather than only forwards, because
upstream data is restated — subscription events get backdated, and a payment
processor can revise a settled charge for days. `txn_date > max(txn_date)`
would miss every one of those corrections, so the fact table reprocesses a
trailing window and `delete+insert` on `txn_id` keeps the reprocess idempotent
instead of double-counting it. Both windows are `vars` in `dbt_project.yml`.

## Data quality

- **dbt tests:** `unique`, `not_null`, `accepted_values` (plan, status, platform, event_type), and `relationships` across dims/facts.
- **Singular tests:** MRR non-negative, retention rate within [0, 1], Type 2
  windows contiguous and non-overlapping, exactly one open version per
  subscription, and every charge attributed to a validity window.
- **Quality gate:** `quality/run_checks.py` re-checks PK uniqueness, referential integrity, MRR sign, churn sanity, the Type 2 chain invariants,
  point-in-time attribution coverage, and a freshness SLA, then writes `artifacts/quality_report.json` and exits non-zero on failure (used as the CI gate).
