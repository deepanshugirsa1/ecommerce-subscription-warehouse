"""One-command local pipeline: generate -> ingest -> dbt build -> quality gates.

Run: python run_demo.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

STEPS = [
    ("Generate raw data", [sys.executable, "data/generate_data.py"]),
    ("Ingest into lakehouse", [sys.executable, "spark/ingest_subscriptions.py"]),
    ("Build dbt models + tests", ["dbt", "build", "--profiles-dir", "."]),
    ("Run data-quality gates", [sys.executable, "quality/run_checks.py"]),
]


def main() -> int:
    for label, cmd in STEPS:
        print(f"\n=== {label} ===")
        result = subprocess.run(cmd, cwd=ROOT)
        if result.returncode != 0:
            print(f"Step failed: {label}")
            return result.returncode
    print("\nPipeline complete. See artifacts/quality_report.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
