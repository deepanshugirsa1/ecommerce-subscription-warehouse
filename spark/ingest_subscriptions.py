"""Spark-style raw ingest into the local lakehouse.

Reads raw CSVs, lands them as columnar Parquet (the "curated lake"), and
registers them as raw_* tables inside the DuckDB warehouse so dbt can model
them through governed sources. In production this is an EMR/Glue PySpark job
writing Parquet to S3 and cataloging it; locally we keep the same shape.

Run: python spark/ingest_subscriptions.py
"""
from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
CURATED = ROOT / "data" / "curated"
CURATED.mkdir(parents=True, exist_ok=True)
DB = ROOT / "data" / "warehouse.duckdb"

con = duckdb.connect(str(DB))
loaded = 0
for csv in sorted(RAW.glob("*.csv")):
    name = csv.stem
    df = pd.read_csv(csv, dtype=str, keep_default_na=False)
    parquet = CURATED / f"{name}.parquet"
    df.to_parquet(parquet, index=False)
    con.execute(
        f"CREATE OR REPLACE TABLE raw_{name} AS "
        f"SELECT * FROM read_parquet('{parquet.as_posix()}')"
    )
    loaded += len(df)
    print(f"Ingested {name}: {len(df)} rows -> parquet + raw_{name}")

con.close()
print(f"Lakehouse ingest complete: {loaded} total rows into {DB.name}")
