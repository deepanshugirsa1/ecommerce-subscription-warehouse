import pandas as pd
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
OUT = Path(__file__).resolve().parents[1] / "data" / "curated"
OUT.mkdir(parents=True, exist_ok=True)

for f in RAW.glob("*.csv"):
    df = pd.read_csv(f)
    df.to_parquet(OUT / f"{f.stem}.parquet", index=False)
    print(f"Ingested {f.name} -> {len(df)} rows")
