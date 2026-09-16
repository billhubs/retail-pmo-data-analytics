import pandas as pd
import re

# 1. Load data dari Silver Layer
df = pd.read_csv('data/processed/shein_master_cleaned.csv', low_memory=False)

# 2. Extract persentase diskon dari string (misal '-20%' atau '20% OFF' -> 20.0)
def parse_discount(val):
    if pd.isna(val):
        return 0.0
    match = re.search(r'(\d+)', str(val))
    return float(match.group(1)) if match else 0.0

df['discount_pct'] = df['discount'].apply(parse_discount)

# 3. Standardisasi nama kolom ke snake_case
df.columns = (
    df.columns.str.lower()
    .str.replace(' ', '_')
    .str.replace('-', '_')
)

# 4. Simpan ke Gold Layer
output_path = 'data/processed/shein_gold_master.csv'
df.to_csv(output_path, index=False)
print(f"=== GOLD LAYER CREATED: {output_path} ===")
print(df[['price_clean', 'discount_pct']].describe())