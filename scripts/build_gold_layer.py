import os
import numpy as np
import pandas as pd


def main():
    input_path = "data/processed/shein_clustered_features.csv"
    output_path = "data/processed/shein_gold_master.csv"

    if not os.path.exists(input_path):
        print(f"Error: {input_path} tidak ditemukan!")
        return

    df = pd.read_csv(input_path)
    np.random.seed(42)

    # 1. Simulasikan Sales Velocity Proxy
    base_velocity = np.random.randint(150, 600, size=len(df))
    discount_boost = 1 + (df["discount_pct"].fillna(0) / 100) * 1.5
    df["est_units_sold"] = (base_velocity * discount_boost).astype(int)

    # 2. Financial & Margin Breakdown
    df["est_gmv"] = df["est_units_sold"] * df["price_cleaned"]

    original_price = np.where(
        df["discount_pct"] > 0,
        df["price_cleaned"] / (1 - (df["discount_pct"] / 100)),
        df["price_cleaned"],
    )
    df["discount_erosion_usd"] = df[
        "est_units_sold"
    ] * (original_price - df["price_cleaned"])

    # COGS (~35% of original price)
    est_cogs = original_price * 0.35

    # 3. Logistics & Freight Cost Model (Per-category weight proxy)
    heavy_categories = [
        "Furniture",
        "Home Textile",
        "Shoes",
        "Appliances",
        "Toys And Games",
    ]
    df["unit_freight_cost"] = np.where(
        df["category"].isin(heavy_categories), 4.50, 1.80
    )
    df["total_freight_cost"] = df["est_units_sold"] * df["unit_freight_cost"]

    # 4. Warehouse Holding Cost Drag (Higher fees for low velocity / high inventory)
    df["unit_holding_cost"] = np.where(
        df["est_units_sold"] < 250, 1.25, 0.45
    )
    df["total_holding_cost"] = df["est_units_sold"] * df["unit_holding_cost"]

    # 5. Net Delivered Margin (Final Bottom-Line Profit)
    df["est_net_margin_usd"] = (
        (df["price_cleaned"] - est_cogs) * df["est_units_sold"]
    ) - (df["total_freight_cost"] + df["total_holding_cost"])

    # 6. CRM Persona Segment Mapping
    crm_conditions = [
        (df["discount_pct"] > 35),
        (df["price_cleaned"] > 40) & (df["discount_pct"] <= 20),
    ]
    crm_choices = [
        "Promo Hunters (Low Retention)",
        "High-LTV Buyers (Brand Loyal)",
    ]
    df["crm_segment"] = np.select(
        crm_conditions, crm_choices, default="Core Regulars (Stable)"
    )

    # 7. Aggregate to Gold Master Level
    gold_summary = (
        df.groupby(["category", "cluster_id"])
        .agg(
            total_skus=("product_name", "count"),
            avg_price=("price_cleaned", "mean"),
            avg_discount=("discount_pct", "mean"),
            total_units_sold=("est_units_sold", "sum"),
            total_gmv=("est_gmv", "sum"),
            total_discount_erosion=("discount_erosion_usd", "sum"),
            total_freight_cost=("total_freight_cost", "sum"),
            total_holding_cost=("total_holding_cost", "sum"),
            total_net_margin=("est_net_margin_usd", "sum"),
            primary_crm_segment=(
                "crm_segment",
                lambda x: x.mode()[0] if not x.empty else "Core Regulars",
            ),
        )
        .reset_index()
    )

    # Rounding Data
    gold_summary["avg_price"] = gold_summary["avg_price"].round(2)
    gold_summary["avg_discount"] = gold_summary["avg_discount"].round(1)
    gold_summary["total_gmv"] = gold_summary["total_gmv"].round(2)
    gold_summary["total_discount_erosion"] = gold_summary[
        "total_discount_erosion"
    ].round(2)
    gold_summary["total_freight_cost"] = gold_summary[
        "total_freight_cost"
    ].round(2)
    gold_summary["total_holding_cost"] = gold_summary[
        "total_holding_cost"
    ].round(2)
    gold_summary["total_net_margin"] = gold_summary["total_net_margin"].round(
        2
    )

    # Strategic Action Rules Engine
    def assign_action(row):
        if row["total_net_margin"] > 40000 and row["avg_discount"] < 25:
            return "SCALE-UP (High Net Yield)"
        elif row["total_holding_cost"] > 15000:
            return "CLEARANCE / CUT (High Storage Drag)"
        elif row["total_discount_erosion"] > 25000:
            return "RISK AWARE (Promo Erosion)"
        else:
            return "MAINTAIN (Stable Flow)"

    gold_summary["strategic_action"] = gold_summary.apply(
        assign_action, axis=1
    )

    gold_summary.to_csv(output_path, index=False)
    print(f"=== GOLD MASTER UPDATED WITH LOGISTICS & CRM: {output_path} ===")


if __name__ == "__main__":
    main()