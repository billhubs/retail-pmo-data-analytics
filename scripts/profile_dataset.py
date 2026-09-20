import glob
import os
import pandas as pd


def profile_raw_data():
    raw_files = glob.glob("data/raw/*.csv")

    if not raw_files:
        print("Error: Tidak ada file CSV di folder data/raw/")
        return

    print("=" * 60)
    print("      DATA PROFILING REPORT (BRONZE / RAW LAYER)      ")
    print("=" * 60)
    print(f"Total Raw Files Found: {len(raw_files)}\n")

    total_rows = 0

    for file_path in raw_files:
        file_name = os.path.basename(file_path)
        try:
            df = pd.read_csv(file_path)
            rows, cols = df.shape
            total_rows += rows

            print(f"📄 File: {file_name}")
            print(f"   - Dimensions: {rows} rows x {cols} columns")
            print(f"   - Columns   : {list(df.columns)}")

            # Check missing values
            null_info = df.isnull().sum()
            null_cols = null_info[null_info > 0]
            if not null_cols.empty:
                print("   - Missing Values:")
                for col, count in null_cols.items():
                    pct = (count / rows) * 100
                    print(f"     * {col}: {count} nulls ({pct:.1f}%)")
            else:
                print("   - Missing Values: None")

            print("-" * 60)

        except Exception as e:
            print(f"❌ Error reading {file_name}: {e}")

    print(f"\nTotal Dataset Size Across All Files: {total_rows:,} rows")
    print("=" * 60)


if __name__ == "__main__":
    profile_raw_data()