# Roadmap to 100%

## Phase 1 (~60%)
- [x] Subscription, transaction, device-registration seeds
- [x] Conformed star-schema dbt marts
- [x] Freshness SLA tests in schema.yml
- [x] PySpark-style ingestion stub

## Phase 2 (70-85%)
- [ ] AWS Glue catalog + EMR PySpark jobs
- [ ] Redshift production deployment
- [ ] Tableau self-service dashboards (retention, MRR, device funnel)
- [ ] Lineage documentation

## Phase 3 (85-100%)
- [ ] Near-real-time subscription event stream (Kinesis)
- [ ] Automated anomaly detection on MRR metrics
- [ ] CI/CD with GitHub Actions + dbt Cloud
