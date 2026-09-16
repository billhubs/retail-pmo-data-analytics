import os
import pandas as pd

RAW_DIR = os.path.join("data", "raw")
PROCESSED_DIR = os.path.join("data", "processed")
os.makedirs(PROCESSED_DIR, exist_ok=True)

def process_all_datasets():
    all_dfs = []
    
    print("=== STARTING BATCH DATA CLEANING ===")
    
    for filename in os.listdir(RAW_DIR):
        if filename.endswith(".csv"):
            file_path = os.path.join(RAW_DIR, filename)
            df = pd.read_csv(file_path)
            
            # 1. Drop unused scrap columns (Schema Pruning)
            cols_to_drop = [c for c in df.columns if 'jump' in c]
            df = df.drop(columns=cols_to_drop)
            
            # 2. Extract Category Name from Filename
            category_name = filename.replace("us-shein-", "").rsplit("-", 1)[0].replace("_", " ").title()
            df['category'] = category_name
            
            # 3. Clean & Convert Price to Numeric (Float64)
            if 'price' in df.columns:
                df['price_clean'] = df['price'].astype(str).str.replace('$', '', regex=False)
                df['price_clean'] = pd.to_numeric(df['price_clean'], errors='coerce')
                
                # Filter invalid prices
                df = df[df['price_clean'].notnull() & (df['price_clean'] > 0)]
            
            # 4. Handle Discount (Domain Default Imputation)
            if 'discount' in df.columns:
                df['discount'] = df['discount'].fillna('0%')
                
            all_dfs.append(df)
            print(f"[CLEANED] {filename} -> Category: {category_name}")

    # Combine into Master Cleaned Data
    master_df = pd.concat(all_dfs, ignore_index=True)
    
    output_master_path = os.path.join(PROCESSED_DIR, "shein_master_cleaned.csv")
    master_df.to_csv(output_master_path, index=False)
    
    print("\n=== BATCH CLEANING COMPLETE ===")
    print(f"Total Combined SKUs: {len(master_df)}")
    print(f"Master file saved to: {output_master_path}")

if __name__ == "__main__":
    process_all_datasets()