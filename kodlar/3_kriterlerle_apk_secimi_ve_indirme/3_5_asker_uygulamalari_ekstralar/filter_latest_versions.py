import pandas as pd

# 1. Load the data
# Using encoding='utf-8' but script itself contains no special chars
input_file = 'bulunan_askeri_uygulamalar.csv'
output_file = 'en_guncel_askeri_uygulamalar.csv'

try:
    df = pd.read_csv(input_file)

    # 2. Ensure vercode is numeric for correct sorting
    df['vercode'] = pd.to_numeric(df['vercode'], errors='coerce')

    # 3. Sort values
    # First by package name, then by vercode (highest first), 
    # then by scan date (latest first) as a backup
    df = df.sort_values(
        by=['pkg_name', 'vercode', 'vt_scan_date'], 
        ascending=[True, False, False]
    )

    # 4. Keep only the first occurrence of each package name
    # This keeps the highest version/latest scan
    df_latest = df.drop_duplicates(subset=['pkg_name'], keep='first')

    # 5. Save the results
    df_latest.to_csv(output_file, index=False)

    print("--- Process Completed ---")
    print(f"Input records: {len(df)}")
    print(f"Unique apps found: {len(df_latest)}")
    print(f"Saved to: {output_file}")

except Exception as e:
    print(f"Error: {e}")
