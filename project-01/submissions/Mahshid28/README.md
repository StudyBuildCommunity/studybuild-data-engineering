# FMCG Inventory Data Integration Pipeline

## Business Problem & 100RFS Connection

FMCG companies with multiple warehouses receive fragmented data (sales, orders, inventory, warehouses) with inconsistent formats, duplicates, and invalid values. This prevents reliable dashboards and optimization models.

**Inspired by 100RFS initiative** (https://aiif.ai/100rfs/) - this project builds the data layer needed for inventory allocation decisions.

> Educational project, not official 100RFS submission.

## Data Sources

| File | Key Fields | Type |
|------|------------|------|
| sales.csv | invoice_no, date, SKU, warehouse, quantity, revenue | Simulated |
| orders.csv | order_id, date, SKU, warehouse, quantity, status | Simulated |
| inventory.csv | snapshot_date, SKU, warehouse, on_hand_qty | Simulated |
| warehouses.csv | warehouse_id, name, city, region | Simulated |

## ETL Architecture

Raw Files → EXTRACT → VALIDATE → TRANSFORM → INTEGRATE → ANALYTICS → Outputs

| Step | File | Description |
|------|------|-------------|
| Extract | extract.ipynb | Load raw CSV files |
| Validate | validate.ipynb | Check 6 business rules |
| Transform | transform.ipynb | Standardize columns, dates, text, numbers |
| Integrate | integrate.ipynb | Join tables, verify row counts |
| Analytics | analytics.ipynb | Create inventory view, attention alerts |

## Validation Rules

| Rule | Description |
|------|-------------|
| R1 | No duplicate primary keys |
| R2 | Valid date format (YYYY-MM-DD) |
| R3 | Warehouse ID exists in master |
| R4 | SKU exists in master list |
| R5 | No negative quantities |
| R6 | Order status is valid |

## How to Run

```bash
# 1. Clone & setup
git clone <repo-url>
cd fmcg-inventory-etl
python -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Place raw files in data/raw/

# 4. Run pipeline
python run_pipeline.py
```

## Key Quality Results

| File | Rows | Violations | Clean Rows |
|------|------|------------|------------|
| Sales | 1,812 | 1,316 | 496 |
| Orders | 2,213 | 1,496 | 717 |
| Inventory | 2,500 | 1,459 | 1,041 |
| Warehouses | 8 | 0 | 8 |

## Operational Insights

### 1. Out of Stock with Demand (12-15% SKUs)
- **Action**: Automatic reorder alerts, review safety stock

### 2. Overstocked Items (8-10% SKUs)
- **Action**: Markdowns, promotions, transfer between warehouses

### 3. Warehouse Imbalance (20-25% SKUs)
- **Action**: Centralized visibility, transfer process

## Repository Structure
```
fmcg-inventory-etl/
├── README.md
├── requirements.txt
├── run_pipeline.py
├── main.ipynb
├── data/
│   ├── raw/
│   └── processed/
├── src/
│   ├── extract.ipynb
│   ├── transform.ipynb
│   ├── validate.ipynb
│   ├── integrate.ipynb
│   └── analytics.ipynb
├── database/
│   └── inventory.db
└── logs/
    └── audit_*.log
```

## Outputs

- **SQLite Database:** `database/inventory.db`
- **Cleaned CSV Files:** `data/processed/*_cleaned.csv`
- **Integrated Data:** `data/processed/integrated/`
- **Analytics Views:** `data/processed/analytics/`
- **Attention Alerts:** `data/processed/analytics/attention_alerts/`
- **Figures:** `data/processed/figures/`
- **Validation Reports:** `data/processed/validation_reports/`
- **Audit Logs:** `logs/audit_*.log`
