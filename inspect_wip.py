import pandas as pd
import os

folder_path = r'E:\G-AI-1\WIP Status'
files = [f for f in os.listdir(folder_path) if f.endswith('.xls')]
files.sort(reverse=True) # Get the latest file

if files:
    latest_file = os.path.join(folder_path, files[0])
    print(f"Analyzing file: {latest_file}")
    
    # Read the file
    df = pd.read_excel(latest_file)
    
    # Print columns to verify
    print("\nColumns found:")
    print(df.columns.tolist())
    
    # Inspect relevant columns
    cols_to_check = ['center_code', 'station_code', 'eng_num']
    existing_cols = [c for c in cols_to_check if c in df.columns]
    
    print("\nData Preview:")
    print(df[existing_cols].head(10))
    
    # Summary of unique center codes (2nd and 3rd chars)
    if 'center_code' in df.columns:
        df['city_code'] = df['center_code'].astype(str).str[1:3]
        print("\nCity Code Summary:")
        print(df['city_code'].value_counts())
else:
    print("No .xls files found.")
