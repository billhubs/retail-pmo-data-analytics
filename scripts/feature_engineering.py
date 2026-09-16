import pandas as pd

# 1. Load data Gold Layer
df = pd.read_csv('data/processed/shein_gold_master.csv', low_memory=False)

# 2. Flag diskon ekstrem (> 50%)
df['is_deep_discount'] = df['discount_pct'] > 50.0

# 3. Buat segmentasi tier harga
def categorize_price(price):
    if price <= 5.0:
        return 'Budget (< $5)'
    elif price <= 15.0:
        return 'Mid-Tier ($5-$15)'
    else:
        return 'Premium (> $15)'

df['price_tier'] = df['price_clean'].apply(categorize_price)

# 4. Simpan dataset final
output_path = 'data/processed/shein_final_features.csv'
df.to_csv(output_path, index=False)

print(f"=== FEATURE ENGINEERING COMPLETE: {output_path} ===")
print("\n--- DISTRIBUSI PRICE TIER ---")
print(df['price_tier'].value_counts())
print("\n--- BARANG DISKON EKSTREM (>50%) ---")
print(df['is_deep_discount'].value_counts())