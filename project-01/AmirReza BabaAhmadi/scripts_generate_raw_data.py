"""
Synthetic FMCG raw data generator.

Simulates a realistic-but-messy extract that mirrors "Approach B" in the
project roadmap: real-world-style transaction/order/inventory columns
combined with a simulated warehouse network, deliberately seeded with the
data quality problems the roadmap calls out (inconsistent headers, mixed
date formats, negative quantities, missing/mismatched warehouse IDs,
duplicate rows, blank SKUs, and status-text typos).

Run once to (re)build data/raw/*.csv. Seeded for reproducibility.
"""
import numpy as np
import pandas as pd
from pathlib import Path

RNG = np.random.default_rng(42)
RAW = Path(__file__).parent / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Master warehouse list (8 warehouses; one referenced elsewhere but NOT
# listed here on purpose, to create a dangling foreign key: WH-09)
# ---------------------------------------------------------------------------
WAREHOUSES = pd.DataFrame({
    "warehouse_id": ["WH-01", "WH-02", "WH-03", "WH-04", "WH-05", "WH-06", "WH-07", "WH-08"],
    "warehouse_name": ["North DC", "South DC", "East Hub", "West Hub", "Central DC",
                        "Coastal Hub", "Metro DC", "Border Hub"],
    "city": ["Tabriz", "Shiraz", "Mashhad", "Ahvaz", "Tehran", "Bandar Abbas", "Isfahan", "Zahedan"],
    "region": ["Northwest", "South", "Northeast", "Southwest", "Central",
               "South", "Central", "Southeast"],
})
WAREHOUSES.to_csv(RAW / "warehouses.csv", index=False)

SKUS = [f"SKU-{i:04d}" for i in range(1, 46)]
VALID_WH = WAREHOUSES["warehouse_id"].tolist()
# a couple of "dirty" warehouse id spellings that should normalize back to a valid id
DIRTY_WH_VARIANTS = {"WH-01": ["wh-01", " WH-01 ", "Wh-01"], "WH-05": ["wh-05", "WH_05"]}

N_DAYS = 70  # ~10 weeks of history ending "today"
END_DATE = pd.Timestamp("2026-09-01")
DATES = pd.date_range(end=END_DATE, periods=N_DAYS, freq="D")


def messy_date(ts, bad_rate=0.18) -> str:
    ts = pd.Timestamp(ts)
    r = RNG.random()
    if r < bad_rate / 3:
        return ts.strftime("%m/%d/%Y")          # US format
    elif r < 2 * bad_rate / 3:
        return ts.strftime("%d-%b-%Y")           # 15-Jan-2026
    elif r < bad_rate:
        return ""                                 # missing
    return ts.strftime("%Y-%m-%d")


def maybe_dirty_wh(wh: str) -> str:
    if wh in DIRTY_WH_VARIANTS and RNG.random() < 0.15:
        return RNG.choice(DIRTY_WH_VARIANTS[wh])
    if RNG.random() < 0.01:
        return "WH-99"        # completely unknown warehouse id
    if RNG.random() < 0.01:
        return "WH-09"        # dangling FK: real-looking id, not in master list
    return wh


# ---------------------------------------------------------------------------
# sales.csv  (messy headers on purpose: TransactionID, SaleDate, SKU , ...)
# ---------------------------------------------------------------------------
n_sales = 1850
rows = []
for i in range(n_sales):
    d = RNG.choice(DATES)
    wh = RNG.choice(VALID_WH)
    sku = RNG.choice(SKUS)
    qty = int(RNG.poisson(18))
    if RNG.random() < 0.02:               # unflagged negative (data-entry error)
        qty = -abs(qty) - 1
    revenue = round(max(qty, 0) * RNG.uniform(2.5, 40.0), 2)
    rows.append({
        "TransactionID": f"TXN{i:06d}",
        "SaleDate ": messy_date(d),
        " SKU": sku if RNG.random() > 0.01 else "",     # ~1% blank sku
        "Warehouse_ID": maybe_dirty_wh(wh),
        " Quantity": qty if RNG.random() > 0.015 else "",  # ~1.5% blank qty
        "Revenue": revenue,
    })
sales_df = pd.DataFrame(rows)
# inject ~1.5% exact-duplicate rows (same transaction re-sent)
dupe_idx = RNG.choice(sales_df.index, size=int(n_sales * 0.015), replace=False)
sales_df = pd.concat([sales_df, sales_df.loc[dupe_idx]], ignore_index=True)
sales_df = sales_df.sample(frac=1, random_state=1).reset_index(drop=True)
sales_df.to_csv(RAW / "sales.csv", index=False)

# ---------------------------------------------------------------------------
# orders.csv (messy status text, mixed casing, malformed dates)
# ---------------------------------------------------------------------------
STATUS_VARIANTS = ["Pending", "pending ", "PENDING", "Shipped", "shiped", "Cancelled",
                    "cancelled", "CANCELLED", "Delivered", "delivered"]
n_orders = 760
rows = []
for i in range(n_orders):
    d = RNG.choice(DATES)
    wh = RNG.choice(VALID_WH)
    sku = RNG.choice(SKUS)
    qty = int(RNG.poisson(45))
    if RNG.random() < 0.015:
        qty = -qty - 1
    rows.append({
        "OrderID": f"ORD{i:06d}",
        "Order Date": messy_date(d, bad_rate=0.15),
        "Sku": sku,
        "WarehouseID": maybe_dirty_wh(wh),
        "OrderedQty": qty if RNG.random() > 0.01 else "",
        "Status": RNG.choice(STATUS_VARIANTS),
    })
orders_df = pd.DataFrame(rows)
dupe_idx = RNG.choice(orders_df.index, size=int(n_orders * 0.01), replace=False)
orders_df = pd.concat([orders_df, orders_df.loc[dupe_idx]], ignore_index=True)
orders_df = orders_df.sample(frac=1, random_state=2).reset_index(drop=True)
orders_df.to_csv(RAW / "orders.csv", index=False)

# ---------------------------------------------------------------------------
# inventory.csv (weekly snapshots per sku/warehouse; some negative on-hand,
# a handful of exact duplicate sku+warehouse+date rows)
# ---------------------------------------------------------------------------
SNAP_DATES = pd.date_range(end=END_DATE, periods=10, freq="7D")
rows = []
for d in SNAP_DATES:
    for wh in VALID_WH:
        for sku in SKUS:
            if RNG.random() < 0.04:      # not every sku stocked at every wh every week
                continue
            qty = int(RNG.normal(120, 60))
            if RNG.random() < 0.01:
                qty = -abs(qty) - 1        # data entry error, should be flagged/dropped
            rows.append({
                "SnapshotDate": messy_date(d, bad_rate=0.10),
                "SKU": sku,
                "WarehouseID": maybe_dirty_wh(wh),
                "OnHandQty": qty,
            })
inv_df = pd.DataFrame(rows)
dupe_idx = RNG.choice(inv_df.index, size=25, replace=False)
inv_df = pd.concat([inv_df, inv_df.loc[dupe_idx]], ignore_index=True)
inv_df = inv_df.sample(frac=1, random_state=3).reset_index(drop=True)
inv_df.to_csv(RAW / "inventory.csv", index=False)

print("Raw files written to", RAW)
for f in ["warehouses.csv", "sales.csv", "orders.csv", "inventory.csv"]:
    df = pd.read_csv(RAW / f)
    print(f"  {f}: {len(df)} rows, columns={list(df.columns)}")
