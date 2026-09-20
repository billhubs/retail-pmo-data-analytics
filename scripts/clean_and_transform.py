import glob
import os
import re
import pandas as pd


def parse_price(val):
    if pd.isna(val):
        return None
    match = re.search(r"\d+(\.\d+)?", str(val))
    return float(match.group()) if match else None


def parse_discount(val):
    if pd.isna(val):
        return 0.0
    match = re.search(r"\d+", str(val))
    return float(match.group()) if match else 0.0


def main():
    raw_files = glob.glob("data/raw/*.csv")
    if not raw_files:
        print("Error: Tidak ada file CSV di data/raw/")
        return

    df_list = []
    for file in raw_files:
        temp_df = pd.read_csv(file)
        temp_df.columns = temp_df.columns.str.strip().str.lower()

        # Ekstrak nama kategori dari nama file
        cat_name = (
            os.path.basename(file)
            .replace("us-shein-", "")
            .rsplit("-", 1)[0]
            .replace("_", " ")
            .title()
        )

        # Handle nama kolom produk
        title_col = (
            "goods-title-link"
            if "goods-title-link" in temp_df.columns
            else temp_df.columns[0]
        )
        temp_df["product_name"] = temp_df[title_col]
        temp_df["category"] = cat_name

        # Parse Price
        if "price" in temp_df.columns:
            temp_df["price_cleaned"] = temp_df["price"].apply(parse_price)
        else:
            temp_df["price_cleaned"] = None

        # Parse Discount (null = 0%)
        if "discount" in temp_df.columns:
            temp_df["discount_pct"] = temp_df["discount"].apply(parse_discount)
        else:
            temp_df["discount_pct"] = 0.0

        # Parse Color Count (null = 1 warna)
        if "color-count" in temp_df.columns:
            temp_df["color_count"] = temp_df["color-count"].fillna(1)
        else:
            temp_df["color_count"] = 1.0

        selected_cols = [
            "category",
            "product_name",
            "price_cleaned",
            "discount_pct",
            "color_count",
        ]
        df_list.append(temp_df[selected_cols])

    master = pd.concat(df_list, ignore_index=True)

    # Drop baris yang gak punya nama produk atau harga
    master = master.dropna(subset=["price_cleaned", "product_name"])

    os.makedirs("data/processed", exist_ok=True)
    out_path = "data/processed/shein_master_cleaned.csv"
    master.to_csv(out_path, index=False)
    print(f"=== CLEANING SUCCESS: Saved {len(master):,} rows to {out_path} ===")


if __name__ == "__main__":
    main()