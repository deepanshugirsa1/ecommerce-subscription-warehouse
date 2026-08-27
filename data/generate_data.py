import pandas as pd
from pathlib import Path
import random

base = Path(__file__).parent
(base / "raw").mkdir(parents=True, exist_ok=True)
for name, cols in [
    ("subscriptions", ["sub_id","user_id","plan","status","mrr"]),
    ("transactions", ["txn_id","user_id","amount","device_id"]),
    ("devices", ["device_id","platform","registered_at"]),
]:
    rows = []
    for i in range(200):
        row = {}
        for c in cols:
            if "id" in c:
                row[c] = f"{c[:3]}{i}"
            elif c == "status":
                row[c] = random.choice(["active", "cancelled"])
            elif c == "mrr":
                row[c] = round(random.uniform(9, 99), 2)
            elif c == "amount":
                row[c] = round(random.uniform(5, 200), 2)
            elif c == "platform":
                row[c] = random.choice(["ios", "android"])
            elif c == "registered_at":
                row[c] = f"2025-0{(i % 9) + 1}-15"
            elif c == "plan":
                row[c] = random.choice(["basic", "pro", "enterprise"])
            else:
                row[c] = f"u{i % 30}"
        rows.append(row)
    pd.DataFrame(rows).to_csv(base / "raw" / f"{name}.csv", index=False)
print("Generated subscription, transaction, device data")
