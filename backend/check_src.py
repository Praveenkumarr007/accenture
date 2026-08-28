import pandas as pd, os
src = r'C:\Users\Administrator\Downloads\businessintelligence_7days_extended'
for f in ['sales.csv','marketing.csv','inventory.csv']:
    df = pd.read_csv(os.path.join(src, f))
    print(f"\n=== {f}: {len(df)} rows ===")
    dcol = 'order_date' if f == 'sales.csv' else 'date'
    print(f"  date col: {dcol}")
    if dcol in df.columns:
        print(f"  min: {df[dcol].min()}  max: {df[dcol].max()}")
        print(f"  unique dates: {df[dcol].nunique()}")
        print(f"  sample dates: {sorted(df[dcol].unique())[:5]}")
    else:
        print(f"  columns: {list(df.columns)}")