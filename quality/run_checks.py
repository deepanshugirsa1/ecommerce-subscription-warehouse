"""Post-build data-quality gates + freshness SLA on the subscription warehouse.

Runs independent assertions against the built marts and writes a machine-readable
report to artifacts/quality_report.json. Exits non-zero if any gate fails, so it
can act as a CI quality gate.

Run: python quality/run_checks.py
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "warehouse.duckdb"
ARTIFACTS = ROOT / "artifacts"
ARTIFACTS.mkdir(exist_ok=True)

FRESHNESS_SLA_DAYS = 420  # synthetic data is dated in 2025; generous SLA for demo

con = duckdb.connect(str(DB), read_only=True)


def scalar(sql: str):
    return con.execute(sql).fetchone()[0]


checks = []


def check(name: str, passed: bool, detail: str):
    checks.append({"check": name, "status": "PASS" if passed else "FAIL", "detail": detail})


# 1. Primary-key uniqueness on key marts
for model, key in [("dim_subscriptions", "sub_id"), ("dim_users", "user_id"),
                   ("fct_transactions", "txn_id"), ("mart_mrr_monthly", "month")]:
    dupes = scalar(
        f"select count(*) from (select {key} from {model} group by {key} having count(*) > 1)"
    )
    check(f"unique:{model}.{key}", dupes == 0, f"{dupes} duplicate keys")

# 2. No negative MRR
neg = scalar("select count(*) from mart_mrr_monthly where active_mrr < 0 or new_mrr < 0 or churned_mrr < 0")
check("mrr_non_negative", neg == 0, f"{neg} negative-MRR months")

# 3. Retention within [0,1]
bad_ret = scalar("select count(*) from mart_retention_cohort where retention_rate < 0 or retention_rate > 1")
check("retention_rate_bounds", bad_ret == 0, f"{bad_ret} out-of-range rows")

# 4. Referential integrity: every transaction maps to a known subscription
orphans = scalar(
    "select count(*) from fct_transactions t "
    "left join dim_subscriptions s on s.sub_id = t.sub_id where s.sub_id is null"
)
check("txn_sub_referential_integrity", orphans == 0, f"{orphans} orphan transactions")

# 5. Churn rate is a sane fraction
churn = scalar("select lifetime_churn_rate from mart_subscription_kpis")
check("churn_rate_sane", 0 <= churn <= 1, f"lifetime_churn_rate={churn}")

# Freshness SLA: newest transaction vs today
max_txn = scalar("select max(txn_date) from fct_transactions")
age_days = (date.today() - max_txn).days
fresh = age_days <= FRESHNESS_SLA_DAYS
check("freshness_sla", fresh, f"newest txn {max_txn} ({age_days}d old, SLA {FRESHNESS_SLA_DAYS}d)")

kpis = con.execute(
    "select total_subscriptions, active_subscriptions, current_mrr, arr, "
    "current_arpu, lifetime_churn_rate from mart_subscription_kpis"
).fetchdf().to_dict("records")[0]
con.close()

passed = sum(1 for c in checks if c["status"] == "PASS")
total = len(checks)
report = {
    "status": "HEALTHY" if passed == total else "UNHEALTHY",
    "checks_passed": passed,
    "checks_total": total,
    "pass_rate": round(passed / total, 4),
    "freshness_sla_days": FRESHNESS_SLA_DAYS,
    "kpis": kpis,
    "checks": checks,
}
(ARTIFACTS / "quality_report.json").write_text(json.dumps(report, indent=2, default=str))

print(f"Quality: {passed}/{total} checks passed ({report['status']})")
for c in checks:
    print(f"  [{c['status']}] {c['check']} — {c['detail']}")
print(f"KPIs: {kpis}")

sys.exit(0 if passed == total else 1)
