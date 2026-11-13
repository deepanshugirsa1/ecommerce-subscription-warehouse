"""Airflow DAG that orchestrates the daily subscription-warehouse build.

Mirrors run_demo.py as discrete, retryable tasks with a freshness SLA. This is
the production-shaped orchestration; locally the same steps run via run_demo.py.
"""
from __future__ import annotations

from datetime import datetime, timedelta

try:
    from airflow import DAG
    from airflow.operators.bash import BashOperator
except ImportError:  # keep repo importable without Airflow installed
    DAG = None

default_args = {
    "owner": "data-eng",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "sla": timedelta(hours=6),
}

if DAG is not None:
    with DAG(
        dag_id="subscription_warehouse",
        start_date=datetime(2025, 1, 1),
        schedule_interval="0 6 * * *",
        catchup=False,
        default_args=default_args,
        tags=["subscriptions", "lakehouse", "dbt"],
    ) as dag:
        generate = BashOperator(task_id="generate_data", bash_command="python data/generate_data.py")
        ingest = BashOperator(task_id="ingest_lakehouse", bash_command="python spark/ingest_subscriptions.py")
        build = BashOperator(task_id="dbt_build", bash_command="dbt build --profiles-dir .")
        quality = BashOperator(task_id="quality_gates", bash_command="python quality/run_checks.py")

        generate >> ingest >> build >> quality
