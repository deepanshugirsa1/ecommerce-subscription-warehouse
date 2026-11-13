"""Streamlit self-service dashboard over the subscription marts.

Run: streamlit run app/dashboard.py
"""
from __future__ import annotations

from pathlib import Path

import duckdb
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "warehouse.duckdb"

st.set_page_config(page_title="Subscription Analytics", layout="wide")
st.title("Subscription & Transaction Analytics")

con = duckdb.connect(str(DB), read_only=True)

kpis = con.execute("select * from mart_subscription_kpis").fetchdf().iloc[0]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Active subscriptions", int(kpis["active_subscriptions"]))
c2.metric("Current MRR", f"${kpis['current_mrr']:,.0f}")
c3.metric("ARR", f"${kpis['arr']:,.0f}")
c4.metric("Lifetime churn", f"{kpis['lifetime_churn_rate']*100:,.1f}%")

st.subheader("MRR movement by month")
mrr = con.execute(
    "select month, active_mrr, new_mrr, churned_mrr, net_new_mrr, arpu "
    "from mart_mrr_monthly order by month"
).fetchdf()
st.line_chart(mrr, x="month", y=["active_mrr", "new_mrr", "churned_mrr"])
st.area_chart(mrr, x="month", y="net_new_mrr")

st.subheader("Cohort retention")
ret = con.execute(
    "select cohort_month, month_offset, retention_rate from mart_retention_cohort"
).fetchdf()
pivot = ret.pivot(index="cohort_month", columns="month_offset", values="retention_rate")
st.dataframe(pivot.style.format("{:.0%}", na_rep=""))

st.subheader("Platform funnel")
st.dataframe(con.execute("select * from mart_platform_funnel").fetchdf())

con.close()
