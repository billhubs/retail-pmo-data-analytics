import os
import pandas as pd


def main():
    input_path = "data/processed/shein_master_cleaned.csv"
    if not os.path.exists(input_path):
        print(f"Error: {input_path} tidak ditemukan!")
        return

    df = pd.read_csv(input_path)

    # 1. Feature: Hitung estimasi harga asli sebelum diskon
    df["estimated_original_price"] = df.apply(
        lambda x: round(x["price_cleaned"] / (1 - (x["discount_pct"] / 100)), 2)
        if x["discount_pct"] > 0
        else x["price_cleaned"],
        axis=1,
    )

    # 2. Feature: Segmentation Price Tier
    df["price_tier"] = pd.qcut(
        df["price_cleaned"].rank(method="first"),
        q=3,
        labels=["Low", "Medium", "High"],
    )

    feat_path = "data/processed/shein_final_features.csv"
    df.to_csv(feat_path, index=False)
    print(f"=== FEATURE ENGINEERING SUCCESS: Saved to {feat_path} ===")


if __name__ == "__main__":
    main()