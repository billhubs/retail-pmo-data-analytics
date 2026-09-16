import os
import pandas as pd

DATA_RAW_DIR = os.path.join("data", "raw")
OUTPUT_DIR = os.path.join("data", "processed")

os.makedirs(OUTPUT_DIR, exist_ok=True)
summary_report = []

print("=== PMO DATA QUALITY AUDIT STARTED ===")

if not os.path.exists(DATA_RAW_DIR):
    print(f"[ERROR] Folder {DATA_RAW_DIR} tidak ditemukan!")
else:
    for filename in os.listdir(DATA_RAW_DIR):
        if filename.endswith(".csv"):
            file_path = os.path.join(DATA_RAW_DIR, filename)
            
            try:
                df = pd.read_csv(file_path)
                
                total_rows = len(df)
                total_cols = len(df.columns)
                missing_values = int(df.isnull().sum().sum())
                
                # Detect Price Anomaly Safely
                price_cols = [c for c in df.columns if 'price' in c.lower()]
                invalid_prices = 0
                if price_cols:
                    # Clean string symbols like '$' if present, then coerce to numeric
                    clean_price = df[price_cols[0]].astype(str).str.replace('$', '', regex=False)
                    numeric_price = pd.to_numeric(clean_price, errors='coerce')
                    invalid_prices = int((numeric_price <= 0).sum() + numeric_price.isnull().sum())

                # Check Duplicate SKUs
                sku_cols = [c for c in df.columns if 'sku' in c.lower() or 'id' in c.lower()]
                duplicate_skus = int(df[sku_cols[0]].duplicated().sum()) if sku_cols else 0
                
                category_name = filename.replace("us-shein-", "").rsplit("-", 1)[0]
                
                is_ready = (missing_values == 0) and (invalid_prices == 0) and (duplicate_skus == 0)
                
                summary_report.append({
                    "Category": category_name,
                    "Filename": filename,
                    "Total SKUs": total_rows,
                    "Total Attributes": total_cols,
                    "Missing Values": missing_values,
                    "Invalid Prices": invalid_prices,
                    "Duplicate SKUs": duplicate_skus,
                    "Audit Status": "READY FOR ODOO" if is_ready else "NEEDS CLEANING"
                })
                print(f"[AUDITED] {filename} | {total_rows} SKUs | Missing: {missing_values} | Invalid Price: {invalid_prices}")
                
            except Exception as e:
                print(f"[ERROR] Gagal memproses {filename}: {str(e)}")

    report_df = pd.DataFrame(summary_report)
    output_file = os.path.join(OUTPUT_DIR, "pmo_data_readiness_audit.csv")
    report_df.to_csv(output_file, index=False)
    print(f"\n=== AUDIT COMPLETE ===")
    print(f"Hasil audit tersimpan di: {output_file}")