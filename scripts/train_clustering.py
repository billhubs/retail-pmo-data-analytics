import os
import glob
import re
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

def generate_clusters_and_erp_data():
    print("=== STARTING CLUSTERING & ERP DATA GENERATION PIPELINE ===")

    input_path = os.path.join("data", "processed", "shein_cleaned_silver.csv")
    if not os.path.exists(input_path):
        print(f"Error: File '{input_path}' tidak ditemukan. Jalankan clean_data.py dulu.")
        return

    df = pd.read_csv(input_path)
    print(f"Data Silver Loaded: {df.shape[0]} rows")

    if "price" in df.columns:
        df["price_cleaned"] = df["price"]

    # 1. Feature Selection & Clustering
    features = ["price", "discount_pct", "color_options"]
    X = df[features].copy().fillna(0)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    df["cluster_id"] = kmeans.fit_predict(X_scaled)

    cluster_centers = df.groupby("cluster_id")["price"].mean().sort_values()
    sorted_cluster_ids = cluster_centers.index.tolist()

    label_map = {
        sorted_cluster_ids[0]: "Cluster 0 - Budget / Regular",
        sorted_cluster_ids[1]: "Cluster 1 - High Discount / Promotional",
        sorted_cluster_ids[2]: "Cluster 2 - Premium / Multi-Color",
    }
    df["cluster_label"] = df["cluster_id"].map(label_map)

    df["avg_price"] = df["price"]
    df["price_tier"] = pd.qcut(
        df["price"].rank(method="first"),
        q=3,
        labels=["Low", "Medium", "High"],
    ).astype(str)

    # 2. Assign Mock Product IDs & Stock Levels for Inventory / FIFO
    np.random.seed(42)
    df["sku_id"] = ["SKU-" + str(100000 + i) for i in range(len(df))]
    df["current_stock"] = np.random.randint(10, 500, size=len(df))
    df["fifo_unit_cost"] = (df["price"] * np.random.uniform(0.3, 0.55, size=len(df))).round(2)
    df["fifo_inventory_value"] = (df["current_stock"] * df["fifo_unit_cost"]).round(2)
    df["fifo_batch_date"] = pd.to_datetime('2026-08-01') - pd.to_timedelta(np.random.randint(1, 120, size=len(df)), unit='D')

    # Save Silver
    silver_output = os.path.join("data", "processed", "shein_clustered_features.csv")
    df.to_csv(silver_output, index=False)
    for alias in ["shein_cleaned_silver.csv", "shein_final_features.csv", "shein_master_cleaned.csv"]:
        df.to_csv(os.path.join("data", "processed", alias), index=False)

    print("=== SUCCESS: All Silver Layer CSVs Synchronized ===")

    # 3. Gold Master Aggregation
    crm_map = {
        "Cluster 0 - Budget / Regular": "Core Regulars (Stable)",
        "Cluster 1 - High Discount / Promotional": "Promo Hunters (Low Retention)",
        "Cluster 2 - Premium / Multi-Color": "High-LTV Buyers (Brand Loyal)",
    }
    df["primary_crm_segment"] = df["cluster_label"].map(crm_map)

    action_map = {
        "Cluster 0 - Budget / Regular": "Maintain Stock & Optimize Margin",
        "Cluster 1 - High Discount / Promotional": "Clearance & Restrict Discounting",
        "Cluster 2 - Premium / Multi-Color": "Scale Assortment & VIP Campaigns",
    }
    df["strategic_action"] = df["cluster_label"].map(action_map)

    df_gold = (
        df.groupby(["category", "cluster_id", "cluster_label", "primary_crm_segment", "strategic_action"])
        .agg(
            total_skus=("product_name", "count"),
            total_products=("product_name", "count"),
            total_units_sold=("product_name", lambda x: len(x) * 15),
            avg_price=("price", "mean"),
            avg_discount=("discount_pct", "mean"),
            total_gmv=("price", lambda x: (x * 15).sum()),
            total_warehouse_stock=("current_stock", "sum"),
            total_fifo_val=("fifo_inventory_value", "sum")
        )
        .reset_index()
    )

    df_gold["total_discount_erosion"] = df_gold["total_gmv"] * (df_gold["avg_discount"] / 100.0)
    df_gold["total_freight_cost"] = df_gold["total_units_sold"] * 0.85
    df_gold["total_holding_cost"] = df_gold["total_skus"] * 12.50
    df_gold["total_net_margin"] = (
        df_gold["total_gmv"]
        - df_gold["total_discount_erosion"]
        - df_gold["total_freight_cost"]
        - df_gold["total_holding_cost"]
    )

    gold_output = os.path.join("data", "processed", "shein_gold_master.csv")
    df_gold.to_csv(gold_output, index=False)
    print(f"=== SUCCESS: Gold Master Saved to '{gold_output}' ===")

    # 4. Generate Vendors Master CSV
    vendors_data = [
        {"vendor_id": "VEND-001", "vendor_name": "Global Tex Logistics Co.", "category": "womens_clothing", "address": "100 Supply Way, Los Angeles, CA", "contact": "+1 (310) 555-0144 | ops@globaltex.com", "negotiated_deal": "15% Bulk Discount > 10k units"},
        {"vendor_id": "VEND-002", "vendor_name": "Sino-Pacific Manufacturing", "category": "electronics", "address": "88 Industrial Park, Shenzhen, CN", "contact": "+86 755 8830 1122 | export@sinopacific.cn", "negotiated_deal": "Net-60 Payment Terms + Free Ocean Freight"},
        {"vendor_id": "VEND-003", "vendor_name": "Apex Home & Goods Ltd.", "category": "home_and_kitchen", "address": "45 Freight Road, Chicago, IL", "contact": "+1 (312) 555-0199 | sales@apexgoods.com", "negotiated_deal": "5% Rebate on Quarterly PO > $100k"},
        {"vendor_id": "VEND-004", "vendor_name": "TrendStyle Apparels", "category": "mens_clothes", "address": "12 Fashion Ave, New York, NY", "contact": "+1 (212) 555-0188 | order@trendstyle.com", "negotiated_deal": "Priority Air Express (3 days SLA)"},
        {"vendor_id": "VEND-005", "vendor_name": "OmniBeauty & Care Corp.", "category": "beauty_and_health", "address": "77 Science Blvd, Boston, MA", "contact": "+1 (617) 555-0133 | B2B@omnibeauty.com", "negotiated_deal": "10% Defective Allowance Credit"}
    ]
    pd.DataFrame(vendors_data).to_csv(os.path.join("data", "processed", "vendors_master.csv"), index=False)

    # 5. Generate Purchasing Orders & Demand Log CSV
    sample_skus = df.sample(20, random_state=42)
    po_list = []
    departments = ["Central Operations", "Regional Sales East", "Promo Campaign Team", "E-Commerce Fulfillment", "Category Manager"]
    reasons = [
        "Low stock threshold breach (< 50 units remaining)",
        "Upcoming 10.10 Mega Flash Sale demand spike",
        "High velocity item - Safety stock buffer replenishment",
        "Vendor promo discount deal lock-in before price increase",
        "Backorder queue pending customer fulfillment"
    ]

    for idx, row in sample_skus.iterrows():
        requested_qty = np.random.randint(200, 1500)
        unit_cost = row["fifo_unit_cost"]
        po_list.append({
            "po_number": f"PO-2026-{1000 + len(po_list)}",
            "sku_id": row["sku_id"],
            "product_name": row["product_name"],
            "category": row["category"],
            "demanding_department": np.random.choice(departments),
            "requested_qty": requested_qty,
            "warehouse_current_stock": row["current_stock"],
            "stock_vs_po_gap": row["current_stock"] - requested_qty,
            "unit_cost_usd": unit_cost,
            "total_deal_cost_usd": round(requested_qty * unit_cost, 2),
            "demand_reason": np.random.choice(reasons),
            "vendor_name": "Global Tex Logistics Co." if "clothing" in row["category"] else "Sino-Pacific Manufacturing",
            "po_status": np.random.choice(["Approved", "Pending C-Suite Signoff", "In Transit"])
        })
    pd.DataFrame(po_list).to_csv(os.path.join("data", "processed", "purchasing_orders.csv"), index=False)

    # 6. Generate Delivery Schedule & History Log CSV
    delivery_list = []
    carriers = ["FedEx Freight", "DHL Express", "Maersk Line", "UPS Supply Chain"]
    statuses = ["In Transit", "Delivered", "Scheduled Departure", "Customs Clearance"]

    for idx, po in enumerate(po_list[:12]):
        est_delivery = pd.to_datetime('2026-09-20') + pd.timedelta(np.random.randint(1, 15), unit='D')
        delivery_cost = round(po["requested_qty"] * np.random.uniform(0.4, 1.2), 2)
        delivery_list.append({
            "delivery_id": f"DEL-2026-{500 + idx}",
            "po_number": po["po_number"],
            "carrier_name": np.random.choice(carriers),
            "product_name": po["product_name"],
            "quantity_shipped": po["requested_qty"],
            "origin_warehouse": "Warehouse Port Hub A",
            "destination_warehouse": "Distribution Center West B",
            "dispatch_date": "2026-09-18",
            "est_delivery_date": est_delivery.strftime("%Y-%m-%d"),
            "delivery_cost_usd": delivery_cost,
            "status": np.random.choice(statuses)
        })
    pd.DataFrame(delivery_list).to_csv(os.path.join("data", "processed", "delivery_schedule.csv"), index=False)

    print("=== SUCCESS: All Warehouse & ERP Data Tables Generated Successfully ===")

if __name__ == "__main__":
    generate_clusters_and_erp_data()