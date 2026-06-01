import pandas as pd
import numpy as np

# 設定參數
take_profit = 0.09
stop_loss = 0.046
shares = 1000

# 讀取 Excel
input_file = "E:\\G-AI-1\\Stock analysis\\2330_台積電_EOM_20260430.xlsx"
output_file = "E:\\G-AI-1\\Stock analysis\\2330_台積電_回測結果.xlsx"

print(f"讀取資料: {input_file}")
df = pd.read_excel(input_file)

# 為了避免中文編碼錯誤，我們直接使用 iloc 來取得對應的欄位資料
# 根據我們前面看到的結構：
# 0:日期, 1:開盤, 2:最高, 3:最低, 4:收盤, 5:成交量
# 6:MA5, 7:MA20, 8:MA60, 9:MA120
# 10:EOM, 11:EOM_Signal, 12:MFI, 13:MFI_Signal, 14:MACD

date_col = df.columns[0]
open_col = df.columns[1]
close_col = df.columns[4]
ma20_col = df.columns[7]
eom_col = df.columns[10]
eomsig_col = df.columns[11]
mfi_col = df.columns[12]
macd_col = df.columns[14]

# 確保數值型態
for col in [open_col, close_col, ma20_col, eom_col, eomsig_col, mfi_col, macd_col]:
    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

df['Action'] = ""
df['Trade_Price'] = 0.0
df['PnL'] = 0.0
df['Hold'] = False

hold = False
buy_price = 0.0

for i in range(1, len(df) - 1):
    c = df.iloc[i]
    n = df.iloc[i+1] # next day for trade price
    
    # 取得當前 K 棒的指標
    c_close = c[close_col]
    c_ma20 = c[ma20_col]
    c_eom = c[eom_col]
    c_eomsig = c[eomsig_col]
    c_macd = c[macd_col]
    c_mfi = c[mfi_col]
    
    if not hold:
        # 進場條件 (TSMC V4 邏輯)
        if (c_close > c_ma20) and (c_eom > c_eomsig) and (c_macd > 0) and (c_mfi > 40):
            hold = True
            buy_price = n[open_col]  # 隔天開盤買進
            df.at[i+1, 'Action'] = '買進'
            df.at[i+1, 'Trade_Price'] = buy_price
    else:
        # 獲利或停損判定 (依據隔天開盤價)
        n_open = n[open_col]
        pnl_ratio = (n_open - buy_price) / buy_price if buy_price > 0 else 0
        
        if pnl_ratio >= take_profit or pnl_ratio <= -stop_loss:
            hold = False
            sell_price = n_open # 隔天開盤賣出
            pnl = (sell_price - buy_price) * shares
            
            df.at[i+1, 'Action'] = '賣出'
            df.at[i+1, 'Trade_Price'] = sell_price
            df.at[i+1, 'PnL'] = pnl
            buy_price = 0.0
            
    df.at[i, 'Hold'] = hold

# 計算累積損益
df['Cumulative_PnL'] = df['PnL'].cumsum()

# 儲存到新的 Excel
df.to_excel(output_file, index=False)
print(f"回測完成！已將結果儲存至: {output_file}")
