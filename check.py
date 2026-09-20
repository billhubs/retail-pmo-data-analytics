import os
import glob
import pandas as pd

raw_dir = os.path.join("data", "raw")
csv_files = glob.glob(os.path.join(raw_dir, "*.csv"))

print(f"Ditemukan {len(csv_files)} file CSV di folder '{raw_dir}'.\n")

all_dfs = []

for file_path in csv_files:
    file_name = os.path.basename(file_path)
    print(f"==================================================")
    print(f"FILE: {file_name}")
    print(f"==================================================")
    
    # Read CSV
    df = pd.read_csv(file_path, low_memory=False)
    
    # Tambah kolom penanda asal file
    df['source_file'] = file_name
    all_dfs.append(df)
    
    print("--- Detail Missing Values ---")
    nulls = df.isnull().sum()
    print(nulls[nulls > 0] if nulls.sum() > 0 else "Tidak ada missing value.")
    
    print("\n--- Jumlah Baris & Kolom ---")
    print(f"Shape: {df.shape}")
    print("\n")

# Combine semua dataset bronze layer untuk total summary
if all_dfs:
    combined_df = pd.concat(all_dfs, ignore_index=True)
    print("==================================================")
    print("=== SUMMARY TOTAL BRONZE LAYER (ALL RAW CSVs) ===")
    print("==================================================")
    print(f"Total Combined Shape : {combined_df.shape}")
    print("\n--- Total Missing Values per Kolom ---")
    print(combined_df.isnull().sum())
    print("\n--- Tipe Data Kolom Gabungan ---")
    print(combined_df.dtypes)