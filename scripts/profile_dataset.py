import os
import pandas as pd

file_path = os.path.join("data", "raw", "us-shein-appliances-3987.csv")
df = pd.read_csv(file_path)

print("=== DETAIL MISSING VALUES PER KOLOM ===")
print(df.isnull().sum())

print("\n=== TIPE DATA AKTUAL ===")
print(df.dtypes)