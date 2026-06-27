#!/usr/bin/env python3
"""Seed master tables from CSVs. Run after `alembic upgrade head`.

python migrations/seed.py
"""

import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "acme.db"
SEED_DIR = ROOT / "data" / "seed"

SEEDS = {
    "inventory.csv": "master_inventory",
    "merchants.csv": "master_merchants",
}


def main() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        for filename, table in SEEDS.items():
            df = pd.read_csv(SEED_DIR / filename)
            df.to_sql(table, conn, if_exists="append", index=False)
            print(f"seeded {table:<25} {len(df)} rows")


if __name__ == "__main__":
    main()
