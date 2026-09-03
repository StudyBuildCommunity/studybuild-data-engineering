from src.extract import extract_all
from src.transform import transform_all
from src.integrate import (
    integrate_sales,
    integrate_orders,
    create_inventory_summary,
)
from src.business import create_business_ready_inventory
from src.load import load_database
from src.transform import PROCESSED_DATA_DIR


def main():
    print("=== ETL PIPELINE START ===")

    print("\n[1/5] Extract")
    datasets = extract_all()

    print("[2/5] Transform")
    transformed = transform_all(datasets)

    print("[3/5] Integration")
    integrated_sales = integrate_sales(
        transformed["sales"],
        transformed["products"],
        transformed["warehouses"],
    )

    integrated_orders = integrate_orders(
        transformed["orders"],
        transformed["products"],
        transformed["warehouses"],
    )

    inventory_summary = create_inventory_summary(
        transformed["inventory"]
    )

    print("[4/5] Business-ready table")
    inventory_business_ready = create_business_ready_inventory(
        transformed["inventory"],
        transformed["sales"],
        transformed["orders"],
        transformed["products"],
        transformed["warehouses"],
    )

    transformed["integrated_sales"] = integrated_sales
    transformed["integrated_orders"] = integrated_orders
    transformed["inventory_summary"] = inventory_summary
    transformed["inventory_business_ready"] = inventory_business_ready

    print("[5/5] Save and load")

    for name, df in transformed.items():
        output_path = PROCESSED_DATA_DIR / f"{name}.csv"
        df.to_csv(output_path, index=False)

    load_database()

    print("\n=== ETL PIPELINE COMPLETE ===")


if __name__ == "__main__":
    main()