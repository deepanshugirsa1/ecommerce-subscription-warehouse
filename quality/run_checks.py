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
                   ("fct_transactions", "txn_id"), ("mart_mrr_monthly", "month"),
                   ("dim_subscription_history", "subscription_version_key")]:
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

# 5. Type 2 history: windows must tile the timeline exactly once per subscription.
#    Overlap double-counts revenue in every point-in-time join; a gap loses a
#    day's charges. Neither shows up as a failure in the fact table itself.
broken_chain = scalar("""
    with chain as (
        select sub_id, version, valid_from, valid_to,
               lead(valid_from) over (partition by sub_id order by version) as next_valid_from
        from dim_subscription_history
    )
    select count(*) from chain
    where next_valid_from is not null
      and (valid_to >= next_valid_from
           or valid_to < valid_from
           or valid_to + interval 1 day <> next_valid_from)
""")
check("scd2_contiguous_windows", broken_chain == 0,
      f"{broken_chain} overlapping, gapped or inverted validity windows")

open_versions = scalar("""
    select count(*) from (
        select sub_id from dim_subscription_history where is_current
        group by sub_id having count(*) <> 1
    )
""")
check("scd2_one_current_version", open_versions == 0,
      f"{open_versions} subscriptions without exactly one open version")

# 6. Point-in-time attribution: every charge lands inside some version window,
#    and lands in exactly one (a fan-out would inflate plan-level revenue).
unattributed = scalar("select count(*) from fct_transactions where subscription_version_key is null")
check("txn_point_in_time_attributed", unattributed == 0,
      f"{unattributed} charges outside every validity window")

restated = scalar("""
    select count(*) from fct_transactions t
    join (select sub_id, plan from dim_subscription_history where is_current) cur
      on cur.sub_id = t.sub_id
    where t.plan_at_txn is not null and t.plan_at_txn <> cur.plan
""")
check("scd2_attribution_differs_from_current", restated > 0,
      f"{restated} charges attributed to a plan other than the current one "
      f"(these are the rows a Type 1 dimension gets wrong)")

# 7. Churn rate is a sane fraction
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
