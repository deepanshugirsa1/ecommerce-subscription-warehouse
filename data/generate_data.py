import pandas as pd
from pathlib import Path
import random

base = Path(__file__).parent
for name, cols in [
    ("subscriptions", ["sub_id","user_id","plan","status","mrr"]),
    ("transactions", ["txn_id","user_id","amount","device_id"]),
    ("devices", ["device_id","platform","registered_at"]),
]:
    rows = [{c: f"{c[:3]}{i}" if "id" in c else random.choice(["active","cancelled"]) if c=="status" else round(random.uniform(9,99),2) if c=="mrr" else random.choice(["ios","android"]) if c=="platform" else f"u{i%30}" for c in cols} for i in range(200)]
    pd.DataFrame(rows).to_csv(base / "raw" / f"{name}.csv", index=False)
    (base / "raw").mkdir(parents=True, exist_ok=True)
print("Generated subscription, transaction, device data")
