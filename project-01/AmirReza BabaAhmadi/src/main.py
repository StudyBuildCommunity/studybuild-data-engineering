"""
FMCG Inventory Data Integration Pipeline — single entry point.

Run: python src/main.py
Order (matches the roadmap's Q1-Q8 checklist):
  1. Extract   4 raw CSVs
  2. Profile   (Q1) raw data quality
  3. Transform (Q3) standardize names/types + Validate (Q2) business rules
  4. Integrate (Q4) safe merges, unmatched rows captured
  5. Build the business-ready analytic view (Q5)
  6. Add operational flags (Q6)
  7. Load into SQLite (Q7) + post-load quality checks
  8. Save charts + a machine-readable quality summary (used by the reports)
"""
import json
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from . import extract, transform, load
from .profile import profile_dataframe
from .logging_config import get_logger

log = get_logger()

ROOT = Path(__file__).resolve().parent.parent
FIG_DIR = ROOT / "figures"
REPORTS_DIR = ROOT / "reports"
PROCESSED_DIR = ROOT / "data" / "processed"
FIG_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

AS_OF = pd.Timestamp("2026-09-01")


def main():
    log.info("=== PIPELINE START ===")
    summary = {"as_of": str(AS_OF.date())}

    # 1. Extract ------------------------------------------------------------
    raw = extract.read_all()

    # 2. Profile (Q1) ---------------------------------------------------------
    valid_wh_preview = None
    profiles = {}
    profiles["warehouses"] = profile_dataframe(raw["warehouses"], "warehouses", key_cols=["warehouse_id"])
    valid_wh_ids = set(
        raw["warehouses"]
        .rename(columns=lambda c: c.strip().lower())
        .pipe(transform.normalize_ids, ["warehouse_id"])
        .loc[:, "warehouse_id"]
        .dropna()
    )

    profiles["sales"] = profile_dataframe(
        raw["sales"], "sales", key_cols=["transaction_id"], date_cols=["sale_date"],
        qty_cols=["quantity"], sku_col="sku", wh_col="warehouse_id", valid_warehouse_ids=valid_wh_ids)
    profiles["orders"] = profile_dataframe(
        raw["orders"], "orders", key_cols=["order_id"], date_cols=["order_date"],
        qty_cols=["ordered_qty"], sku_col="sku", wh_col="warehouse_id", valid_warehouse_ids=valid_wh_ids)
    profiles["inventory"] = profile_dataframe(
        raw["inventory"], "inventory", date_cols=["snapshot_date"], qty_cols=["on_hand_qty"],
        sku_col="sku", wh_col="warehouse_id", valid_warehouse_ids=valid_wh_ids)
    summary["raw_profiles"] = profiles
    summary["raw_row_counts"] = {k: len(v) for k, v in raw.items()}

    # 3. Transform (Q3) + Validate (Q2) -------------------------------------
    warehouses = transform.clean_warehouses(raw["warehouses"])
    valid_wh = set(warehouses["warehouse_id"])
    sales = transform.clean_sales(raw["sales"], valid_warehouse_ids=valid_wh)
    orders = transform.clean_orders(raw["orders"], valid_warehouse_ids=valid_wh)
    inventory = transform.clean_inventory(raw["inventory"], valid_warehouse_ids=valid_wh)

    clean_row_counts = {"warehouses": len(warehouses), "sales": len(sales),
                         "orders": len(orders), "inventory": len(inventory)}
    summary["clean_row_counts"] = clean_row_counts
    summary["rows_dropped"] = {k: summary["raw_row_counts"][k] - clean_row_counts[k] for k in clean_row_counts}
    log.info(f"clean row counts: {clean_row_counts}")

    sales.to_csv(PROCESSED_DIR / "sales_clean.csv", index=False)
    orders.to_csv(PROCESSED_DIR / "orders_clean.csv", index=False)
    inventory.to_csv(PROCESSED_DIR / "inventory_clean.csv", index=False)
    warehouses.to_csv(PROCESSED_DIR / "warehouses_clean.csv", index=False)

    # 4. Integrate (Q4) + 5. Business-ready view (Q5) ------------------------
    analytic, unmatched = transform.build_analytic_view(sales, orders, inventory, warehouses, AS_OF)
    summary["unmatched_counts"] = {k: len(v) for k, v in unmatched.items()}

    # 6. Operational flags (Q6) ----------------------------------------------
    analytic = transform.add_operational_flags(analytic)
    analytic.to_csv(PROCESSED_DIR / "analytic_sku_warehouse.csv", index=False)
    summary["analytic_rows"] = len(analytic)
    summary["flag_counts"] = {
        c: int(analytic[c].sum()) for c in
        ["flag_stockout_risk", "flag_excess_inventory", "flag_order_backlog", "flag_dead_stock"]
    }

    # 7. Load (Q7) ------------------------------------------------------------
    tables = {
        "dim_warehouses": warehouses,
        "fact_sales": sales,
        "fact_orders": orders,
        "fact_inventory": inventory,
        "analytic_sku_warehouse": analytic,
    }
    load_checks = load.load_to_sqlite(tables)
    summary["load_checks"] = load_checks

    # 8. Charts ----------------------------------------------------------------
    plt.style.use("default")

    # Fig 1: total on-hand inventory by warehouse
    inv_by_wh = analytic.groupby("warehouse_name")["on_hand_qty"].sum().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(inv_by_wh.index, inv_by_wh.values, color="#3B6FA0")
    ax.set_title("Total On-Hand Inventory by Warehouse")
    ax.set_ylabel("Units on hand")
    ax.tick_params(axis="x", rotation=35)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig1_inventory_by_warehouse.png", dpi=150)
    plt.close(fig)

    # Fig 2: flagged SKU-warehouse rows by flag type
    flag_counts = summary["flag_counts"]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar([k.replace("flag_", "").replace("_", " ").title() for k in flag_counts],
           list(flag_counts.values()), color="#C0563B")
    ax.set_title("SKU / Warehouse Rows by Operational Flag")
    ax.set_ylabel("Rows flagged")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig2_flags_by_type.png", dpi=150)
    plt.close(fig)

    # Fig 3: top 10 SKUs by on-hand quantity
    top_sku = analytic.groupby("sku")["on_hand_qty"].sum().sort_values(ascending=False).head(10)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.barh(top_sku.index[::-1], top_sku.values[::-1], color="#3B6FA0")
    ax.set_title("Top 10 SKUs by Total On-Hand Quantity")
    ax.set_xlabel("Units on hand")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig3_top_skus_on_hand.png", dpi=150)
    plt.close(fig)

    log.info("Saved 3 figures to figures/")

    # Quality summary -----------------------------------------------------------
    with open(REPORTS_DIR / "quality_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)
    log.info(f"Quality summary written to {REPORTS_DIR / 'quality_summary.json'}")

    log.info("=== PIPELINE END: SUCCESS ===")
    return summary


if __name__ == "__main__":
    main()
