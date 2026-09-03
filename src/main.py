from extract import extract_all
from transform import transform_all
from integrate import (
    integrate_sales,
    integrate_orders,
    create_inventory_summary,
)
from load import load_database


def main() -> None:
    print("=== ETL PIPELINE START ===")

    print("\n[1/4] Extract")
    datasets = extract_all()

    print("[2/4] Transform")
    transformed = transform_all(datasets)

    print("[3/4] Integration")

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

    transformed["integrated_sales"] = integrated_sales
    transformed["integrated_orders"] = integrated_orders
    transformed["inventory_summary"] = inventory_summary

    print("[4/4] Load")

    import transform

    for name, df in transformed.items():
        output_path = (
            transform.PROCESSED_DATA_DIR
            / f"{name}.csv"
        )

        df.to_csv(
            output_path,
            index=False,
        )

    load_database()

    print("\n=== ETL PIPELINE COMPLETE ===")


if __name__ == "__main__":
    main()