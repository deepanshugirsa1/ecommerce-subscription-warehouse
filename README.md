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
        ├─ fct_transactions / fct_subscription_events
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
- dbt: **52 passed** (9 models, 36 tests, 7 views) · quality gates **9/9 HEALTHY** · freshness **PASS**

See [docs/01_metric_definitions.md](docs/01_metric_definitions.md) and
[docs/02_data_dictionary.md](docs/02_data_dictionary.md).

## Data quality

- **dbt tests:** `unique`, `not_null`, `accepted_values` (plan, status, platform, event_type), and `relationships` across dims/facts.
- **Singular tests:** MRR non-negative, retention rate within [0, 1].
- **Quality gate:** `quality/run_checks.py` re-checks PK uniqueness, referential integrity, MRR sign, churn sanity, and a freshness SLA, then writes `artifacts/quality_report.json` and exits non-zero on failure (used as the CI gate).
