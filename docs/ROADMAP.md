# Roadmap

## Complete (local portfolio)
- [x] Realistic subscription-business data generator (users, subscriptions, lifecycle events, transactions, devices)
- [x] Lakehouse ingest: raw CSV -> Parquet lake -> DuckDB raw tables (Spark/EMR-shaped)
- [x] Medallion dbt layering: staging (views) -> intermediate (views) -> marts (tables)
- [x] MRR, churn, ARPU, ARR, cohort-retention, and platform-funnel marts with governed metric definitions
- [x] Data-quality gates: dbt tests (unique, not_null, accepted_values, relationships) + singular MRR/retention assertions
- [x] Standalone quality + freshness-SLA gate writing `artifacts/quality_report.json`
- [x] Airflow DAG (retries + 6h SLA) and one-command `run_demo.py`
- [x] Streamlit self-service dashboard
- [x] GitHub Actions CI running the full pipeline

## Future scope (production)
- [ ] Swap local DuckDB for AWS Glue catalog + EMR PySpark and Redshift/Iceberg marts
- [ ] Near-real-time subscription event stream (Kinesis/Kafka) feeding incremental models
- [ ] Automated anomaly detection on MRR and churn
- [ ] dbt Cloud scheduled jobs and exposures for BI consumers
