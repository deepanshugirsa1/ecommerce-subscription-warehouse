# E-Commerce Subscription & Transaction Analytics Warehouse

Star-schema warehouse modeling subscription, transaction, and device-registration datasets for self-service Tableau reporting and ML downstream use.

> **Status: ~60% complete.** dbt star-schema marts, sample data, and quality tests run locally. AWS Glue/EMR ingestion and Tableau workbook are planned.

## Quickstart

```bash
pip install -r requirements.txt
python data/generate_data.py
python spark/ingest_subscriptions.py
dbt build --profiles-dir .
```

See [docs/ROADMAP.md](docs/ROADMAP.md).
