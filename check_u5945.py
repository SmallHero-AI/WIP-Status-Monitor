import pandas as pd
import glob, os

DATA_FOLDER = r'E:\G-AI-1\WIP Status'
files = glob.glob(os.path.join(DATA_FOLDER, "*.xls"))
latest_file = max(files, key=os.path.getmtime)

print(f"Reading {latest_file}")
df = pd.read_excel(latest_file)
df['eng_num_str'] = df['eng_num'].astype(str).str.strip()
print("Unique eng_nums containing '5945':")
print(df[df['eng_num_str'].str.contains('5945', na=False)]['eng_num_str'].unique())

print("\nRows with eng_num_str == 'U5945':")
print(len(df[df['eng_num_str'] == 'U5945']))
