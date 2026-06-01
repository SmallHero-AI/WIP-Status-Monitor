import pandas as pd
import numpy as np

file_path = "E:\\G-AI-1\\Stock analysis\\2360_致茂_V4_高勝率回測.xlsx"
df_excel = pd.read_excel(file_path, sheet_name="Top1_回測", skiprows=7)
df_excel = df_excel.rename(columns=lambda x: str(x).strip())

df_orig = pd.read_excel("E:\\G-AI-1\\Stock analysis\\Stock original\\2360_致茂_EOM_20260505.xlsx")
df_orig.columns = [str(c) for c in df_orig.columns]
for col in df_orig.columns[1:]:
    df_orig[col] = pd.to_numeric(df_orig[col], errors='coerce').fillna(0)

c_arr, o_arr, h_arr = df_orig.iloc[:, 4].values, df_orig.iloc[:, 1].values, df_orig.iloc[:, 2].values
ma20_arr, ma60_arr = df_orig.iloc[:, 7].values, df_orig.iloc[:, 8].values
eom_arr, eomsig_arr = df_orig.iloc[:, 10].values, df_orig.iloc[:, 11].values
mfi_arr, macd_arr = df_orig.iloc[:, 12].values, df_orig.iloc[:, 14].values

tp, sl, macd, mfi, eom_off = 0.189, 0.08, 2.1, 30, 0.0

hold = False; buy_price = 0.0; pnls = []
python_trades = []

for i in range(2, len(df_orig)-1):
    c_close, n_open = c_arr[i], o_arr[i+1]
    c_ma20, c_eom, c_eomsig, c_macd, c_mfi = ma20_arr[i], eom_arr[i], eomsig_arr[i], macd_arr[i], mfi_arr[i]
    
    if not hold:
        if c_close > c_ma20 and c_eom > (c_eomsig + eom_off) and c_macd > macd and c_mfi > mfi:
            hold = True; buy_price = n_open
            python_trades.append({'action': 'buy', 'date': df_orig.iloc[i+1, 0], 'price': buy_price, 'index': i+1})
    else:
        pnlR = (n_open - buy_price) / buy_price
        if pnlR >= tp or pnlR <= -sl:
            hold = False; pnls.append((n_open - buy_price) * 1000)
            python_trades.append({'action': 'sell', 'date': df_orig.iloc[i+1, 0], 'price': n_open, 'pnl': pnls[-1], 'index': i+1})

excel_trades = []
for idx, row in df_excel.iterrows():
    if row.get('動作(T)') == '買進':
        excel_trades.append({'action': 'buy', 'date': row.iloc[0], 'price': row.get('交易價格(U)'), 'index': idx})
    elif row.get('動作(T)') == '賣出':
        excel_trades.append({'action': 'sell', 'date': row.iloc[0], 'price': row.get('交易價格(U)'), 'pnl': row.get('單筆損益(V)'), 'index': idx})

print(f"Python PnL: {sum(pnls)}")
print(f"Excel PnL: {df_excel['累積損益(W)'].iloc[-1]}")

print("\nDifferences:")
for i in range(max(len(python_trades), len(excel_trades))):
    p_t = python_trades[i] if i < len(python_trades) else None
    e_t = excel_trades[i] if i < len(excel_trades) else None
    
    if p_t != e_t:
        print(f"Trade {i+1}:")
        print(f"  Python: {p_t}")
        print(f"  Excel:  {e_t}")
