import glob
import os
import re
import numpy as np
import pandas as pd


def clean_bronze_layer():
    print("=== STARTING BRONZE TO SILVER ETL PIPELINE ===")

    # Ambil semua file raw CSV
    raw_files = glob.glob(os.path.join("data", "raw", "*.csv"))
    if not raw_files:
        print("Error: Tidak ada file CSV di 'data/raw/'.")
        return

    dfs = []
    for f in raw_files:
        df_temp = pd.read_csv(f, low_memory=False)

        # Ekstrak nama kategori dari nama file (misal: us-shein-appliances-3987.csv -> appliances)
        file_name = os.path.basename(f)
        cat_match = re.search(r"us-shein-(.*?)-\d+\.csv", file_name)
        category_name = cat_match.group(1) if cat_match else "other"

        df_temp["category"] = category_name
        dfs.append(df_temp)

    # Combine semua dataframe
    df = pd.concat(dfs, ignore_index=True)
    print(f"Total Raw Data Loaded: {df.shape[0]} rows")

    # 1. Cleaning Price: Ambil angka desimal (misal '$12.99' -> 12.99)
    if "price" in df.columns:
        df["price_clean"] = (
            df["price"]
            .astype(str)
            .str.extract(r"(\d+\.?\d*)")[0]
            .astype(float)
        )
    else:
        df["price_clean"] = np.nan

    # Drop baris yang tidak punya harga sama sekali (misal 2 baris null tadi)
    df = df.dropna(subset=["price_clean"]).copy()

    # 2. Cleaning Discount: Ambil angka persentase (misal '-20%' -> 20.0, Null -> 0.0)
    if "discount" in df.columns:
        df["discount_clean"] = (
            df["discount"]
            .astype(str)
            .str.extract(r"(\d+)")[0]
            .fillna(0)
            .astype(float)
        )
    else:
        df["discount_clean"] = 0.0

    # 3. Cleaning Color Count: Null diisi 1
    if "color-count" in df.columns:
        df["color_count_clean"] = df["color-count"].fillna(1).astype(int)
    else:
        df["color_count_clean"] = 1

    # 4. Cleaning Product Name
    title_col = (
        "goods-title-link"
        if "goods-title-link" in df.columns
        else "selling_proposition"
    )
    df["product_name"] = df[title_col].fillna("Unknown Product").astype(str)

    # 5. Filter hanya kolom fitur inti untuk Silver Layer
    selected_cols = [
        "product_name",
        "category",
        "price_clean",
        "discount_clean",
        "color_count_clean",
    ]

    df_silver = df[selected_cols].rename(
        columns={
            "price_clean": "price",
            "discount_clean": "discount_pct",
            "color_count_clean": "color_options",
        }
    )

    # Simpan ke folder processed
    os.makedirs(os.path.join("data", "processed"), exist_ok=True)
    output_path = os.path.join("data", "processed", "shein_cleaned_silver.csv")
    df_silver.to_csv(output_path, index=False)

    print(
        f"=== SUCCESS: Cleaned Data Saved to '{output_path}' ({df_silver.shape[0]} rows) ==="
    )
    print("\nPreview Clean Data:")
    print(df_silver.head())


if __name__ == "__main__":
    clean_bronze_layer()