"""Generate a realistic subscription business dataset (deterministic).

Models a SaaS/membership subscription business: users sign up on a plan, pay a
recurring monthly charge, may upgrade/downgrade, and may churn. The output raw
CSVs feed the lakehouse ingest + dbt marts (MRR, churn, ARPU, retention).

Each subscription event carries the plan in force *after* it, which is what
makes a Type 2 history of the subscription dimension reconstructable from the
event stream rather than inferred from a price lookup.

Run: python data/generate_data.py
"""
from __future__ import annotations

import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

SEED = 42
random.seed(SEED)

BASE = Path(__file__).resolve().parent
RAW = BASE / "raw"
RAW.mkdir(parents=True, exist_ok=True)

N_USERS = 600
START = date(2025, 1, 1)
END = date(2025, 12, 31)

PLAN_PRICE = {"basic": 9.00, "pro": 29.00, "enterprise": 99.00}
PLANS = list(PLAN_PRICE.keys())
COUNTRIES = ["US", "CA", "GB", "IN", "DE", "AU"]
CHANNELS = ["organic", "paid_search", "referral", "email", "social"]
PLATFORMS = ["ios", "android", "web"]


def month_floor(d: date) -> date:
    return d.replace(day=1)


def add_months(d: date, n: int) -> date:
    m = d.month - 1 + n
    y = d.year + m // 12
    return date(y, m % 12 + 1, 1)


def rand_date(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, max(delta, 0)))


users, subs, events, txns, devices = [], [], [], [], []

for i in range(N_USERS):
    user_id = f"u{i:04d}"
    # signups weighted toward earlier months so cohorts have tenure to retain
    signup = rand_date(START, date(2025, 10, 31))
    users.append(
        {
            "user_id": user_id,
            "signup_date": signup.isoformat(),
            "country": random.choice(COUNTRIES),
            "acquisition_channel": random.choices(
                CHANNELS, weights=[35, 25, 15, 15, 10]
            )[0],
        }
    )

    # device registrations (1-2 per user)
    for d_ix in range(random.randint(1, 2)):
        devices.append(
            {
                "device_id": f"d{i:04d}{d_ix}",
                "user_id": user_id,
                "platform": random.choices(PLATFORMS, weights=[45, 40, 15])[0],
                "registered_at": rand_date(signup, END).isoformat(),
            }
        )

    # subscription lifecycle
    sub_id = f"s{i:04d}"
    plan = random.choices(PLANS, weights=[50, 35, 15])[0]
    mrr = PLAN_PRICE[plan]
    started = signup
    events.append(
        {
            "event_id": f"e{len(events):05d}",
            "sub_id": sub_id,
            "user_id": user_id,
            "event_type": "created",
            "event_date": started.isoformat(),
            "plan": plan,
            "mrr_change": round(mrr, 2),
        }
    )

    # possible upgrade/downgrade mid-life
    if random.random() < 0.22:
        change_date = rand_date(add_months(started, 1), END)
        new_plan = random.choice([p for p in PLANS if p != plan])
        event_type = "upgraded" if PLAN_PRICE[new_plan] > mrr else "downgraded"
        events.append(
            {
                "event_id": f"e{len(events):05d}",
                "sub_id": sub_id,
                "user_id": user_id,
                "event_type": event_type,
                "event_date": change_date.isoformat(),
                "plan": new_plan,
                "mrr_change": round(PLAN_PRICE[new_plan] - mrr, 2),
            }
        )
        plan, mrr = new_plan, PLAN_PRICE[new_plan]

    # churn with ~40% probability, at a random later month
    cancelled = None
    status = "active"
    if random.random() < 0.40:
        cancelled = rand_date(add_months(started, 1), END)
        status = "cancelled"
        events.append(
            {
                "event_id": f"e{len(events):05d}",
                "sub_id": sub_id,
                "user_id": user_id,
                "event_type": "cancelled",
                "event_date": cancelled.isoformat(),
                "plan": plan,
                "mrr_change": round(-mrr, 2),
            }
        )

    subs.append(
        {
            "sub_id": sub_id,
            "user_id": user_id,
            "plan": plan,
            "status": status,
            "mrr": round(mrr, 2),
            "started_at": started.isoformat(),
            "cancelled_at": cancelled.isoformat() if cancelled else "",
        }
    )

    # recurring monthly transactions for each active month
    txn_month = month_floor(started)
    last_month = month_floor(cancelled) if cancelled else month_floor(END)
    user_devices = [d["device_id"] for d in devices if d["user_id"] == user_id]
    while txn_month <= last_month:
        txns.append(
            {
                "txn_id": f"t{len(txns):06d}",
                "sub_id": sub_id,
                "user_id": user_id,
                "amount": round(mrr, 2),
                "txn_date": txn_month.isoformat(),
                "device_id": random.choice(user_devices),
                "status": "succeeded" if random.random() > 0.03 else "failed",
            }
        )
        txn_month = add_months(txn_month, 1)

pd.DataFrame(users).to_csv(RAW / "users.csv", index=False)
pd.DataFrame(subs).to_csv(RAW / "subscriptions.csv", index=False)
pd.DataFrame(events).to_csv(RAW / "subscription_events.csv", index=False)
pd.DataFrame(txns).to_csv(RAW / "transactions.csv", index=False)
pd.DataFrame(devices).to_csv(RAW / "devices.csv", index=False)

print(
    f"Generated: {len(users)} users, {len(subs)} subscriptions, "
    f"{len(events)} events, {len(txns)} transactions, {len(devices)} devices"
)
