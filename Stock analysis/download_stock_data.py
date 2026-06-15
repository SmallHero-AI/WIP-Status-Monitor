import os
import time
import datetime
import pandas as pd
import numpy as np

# 嘗試載入 yfinance，若未安裝則提供提示
try:
    import yfinance as yf
except ImportError:
    print("⚠️ 偵測到未安裝 yfinance，請在終端機執行: pip install yfinance")
    import sys
    sys.exit(1)

# ==============================================================================
# 1. 參數設定與股票清單
# ==============================================================================
# 熱門股範例清單 (10 檔)，您可以自由擴充至 100 檔
STOCK_LIST = [
    "2330.TW",  # 台積電
    "2454.TW",  # 聯發科
    "2317.TW",  # 鴻海
    "2308.TW",  # 台達電
    "2881.TW",  # 富邦金
    "2882.TW",  # 國泰金
    "2382.TW",  # 廣達
    "2303.TW",  # 聯電
    "2603.TW",  # 長榮
    "3008.TW",  # 大立光
]

# 設定輸出資料夾
OUTPUT_DIR = r"E:\G-AI-1\Stock analysis\data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 為了在計算指標後仍保有完整 900 筆的有效數據，我們向前多下載一些交易日以供計算 MA120 等指標的緩衝
# 900 筆交易日大約需要 1300 個日曆天
CALENDAR_DAYS_TO_DOWNLOAD = 1700 
TARGET_EXPORT_ROWS = 900

# ==============================================================================
# 2. 技術指標計算函數 (標準 Pandas 實作，免除套件版本相依性問題)
# ==============================================================================

def calculate_indicators(df):
    """
    計算 MA5/20/60/120、EOM[60]、Signal[20]、MFI[14]、Signal[9]、MACD (12,26,9)、KD (9,3,3)、RSI (14)
    """
    close = df['Close']
    high = df['High']
    low = df['Low']
    volume = df['Volume']

    # --- A. 移動平均線 (Moving Averages) ---
    df['MA5'] = close.rolling(window=5).mean()
    df['MA20'] = close.rolling(window=20).mean()
    df['MA60'] = close.rolling(window=60).mean()
    df['MA120'] = close.rolling(window=120).mean()

    # --- B. 簡意移動指標 (Ease of Movement, EOM[60]) & 訊號線 (Signal[20]) ---
    # 距離移動 = 今日中點 - 昨日中點
    midpoint_today = (high + low) / 2.0
    midpoint_yesterday = (high.shift(1) + low.shift(1)) / 2.0
    midpoint_move = midpoint_today - midpoint_yesterday
    
    # 區間比率 = (今日成交量 / 100,000,000) / (今日最高價 - 今日最低價)
    high_low_range = high - low
    high_low_range = high_low_range.replace(0, 0.0001)  # 避免除以 0
    box_ratio = (volume / 100000000.0) / high_low_range
    box_ratio = box_ratio.replace(0, 0.0001)  # 避免除以 0
    
    eom_raw = midpoint_move / box_ratio
    df['EOM_60'] = eom_raw.rolling(window=60).mean()
    df['EOM_Signal_20'] = df['EOM_60'].rolling(window=20).mean()

    # --- C. 資金流量指標 (Money Flow Index, MFI[14]) ---
    typical_price = (high + low + close) / 3.0
    raw_money_flow = typical_price * volume
    tp_shift = typical_price.shift(1)
    
    pos_flow = pd.Series(0.0, index=df.index)
    neg_flow = pd.Series(0.0, index=df.index)
    
    pos_flow[typical_price > tp_shift] = raw_money_flow
    neg_flow[typical_price < tp_shift] = raw_money_flow
    
    pos_mf_sum = pos_flow.rolling(window=14).sum()
    neg_mf_sum = neg_flow.rolling(window=14).sum()
    
    mr = pos_mf_sum / neg_mf_sum
    mfi = 100.0 - (100.0 / (1.0 + mr))
    mfi[neg_mf_sum == 0] = 100.0
    mfi[(pos_mf_sum == 0) & (neg_mf_sum == 0)] = 50.0
    df['MFI_14'] = mfi

    # --- D. MACD 指標 (12, 26, 9) ---
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    macd_signal = macd_line.ewm(span=9, adjust=False).mean()
    macd_hist = macd_line - macd_signal  # 柱狀體
    
    df['MACD_Signal_9'] = macd_signal
    df['MACD_Hist'] = macd_hist

    # --- E. KD 指標 (9, 3, 3) (台灣市場常用指數平滑演算法) ---
    low_9 = low.rolling(window=9).min()
    high_9 = high.rolling(window=9).max()
    rsv_range = high_9 - low_9
    rsv = pd.Series(50.0, index=df.index)
    rsv[rsv_range > 0] = (close - low_9) / rsv_range * 100.0
    
    k_list, d_list = [], []
    curr_k, curr_d = 50.0, 50.0
    for idx, rsv_val in rsv.items():
        if pd.isna(low_9[idx]):
            k_list.append(np.nan)
            d_list.append(np.nan)
        else:
            curr_k = curr_k * (2.0/3.0) + rsv_val * (1.0/3.0)
            curr_d = curr_d * (2.0/3.0) + curr_k * (1.0/3.0)
            k_list.append(curr_k)
            d_list.append(curr_d)
            
    df['KD_K'] = k_list
    df['KD_D'] = d_list

    # --- F. 相對強弱指標 (RSI[14]) ---
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    
    # 採用 Wilder's 類似 EMA 的平滑方式計算平均漲跌
    avg_gain = gain.ewm(alpha=1.0/14.0, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0/14.0, adjust=False).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))
    rsi[avg_loss == 0] = 100.0
    df['RSI_14'] = rsi

    return df

# ==============================================================================
# 3. 主執行流程
# ==============================================================================
def main():
    print("[INFO] 開始下載台灣市場歷史股價與計算指標...")
    print(f"[INFO] 儲存目標資料夾: {OUTPUT_DIR}\n")
    
    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=CALENDAR_DAYS_TO_DOWNLOAD)
    
    success_count = 0
    fail_count = 0
    
    for symbol in STOCK_LIST:
        stock_code = symbol.split('.')[0]  # 取得純數字股號 (如 2330)
        print(f"[DOWNLOAD] 正在下載 {symbol} ({stock_code})...", end="", flush=True)
        
        try:
            # 使用 yfinance 下載歷史資料
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date.strftime("%Y-%m-%d"), end=today.strftime("%Y-%m-%d"))
            
            if df.empty or len(df) < 120:
                print(" [失敗: 下載失敗或數據太少，已跳過]")
                fail_count += 1
                continue
                
            # 重設索引使日期成為一般的欄位
            df = df.reset_index()
            # 統一日期格式為 YYYY-MM-DD
            df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
            
            # 計算所有技術指標
            df = calculate_indicators(df)
            
            # 填補計算滾動視窗初期產生的 NaN 數值為 0，避免前端回測解析報錯
            df = df.fillna(0.0)
            
            # 截取最新的 900 筆資料匯出 (以確保所有指標皆已順利計算且有完整值)
            df_export = df.tail(TARGET_EXPORT_ROWS).copy()
            
            # ==================================================================
            # 4. 格式對齊 (配合前端平台的 CSV 索引結構順序)
            # ==================================================================
            # 對齊後欄位索引：
            # 0:日期, 1:開盤價, 2:最高價, 3:最低價, 4:收盤價, 5:成交量, 
            # 6:MA5, 7:MA20, 8:MA60, 9:MA120, 10:EOM[60], 11:Signal[20], 12:MFI[14], 
            # 13:MACD_Signal_9, 14:MACD_Hist (柱狀體), 15:KD_K, 16:KD_D, 17:RSI_14
            export_columns = [
                'Date', 'Open', 'High', 'Low', 'Close', 'Volume',
                'MA5', 'MA20', 'MA60', 'MA120', 'EOM_60', 'EOM_Signal_20', 'MFI_14',
                'MACD_Signal_9', 'MACD_Hist', 'KD_K', 'KD_D', 'RSI_14'
            ]
            
            df_export = df_export[export_columns]
            
            # 設定中文欄位標題 (完美對照原回測 Excel 格式)
            df_export.columns = [
                '日期', '開盤價', '最高價', '最低價', '收盤價', '成交量',
                '均價[5]', '均價[20]', '均價[60]', '均價[120]', 'EOM[60]', 'Signal[20]', 'MFI[14]',
                'Signal[9]', 'MACD 柱狀體[12, 26, 9]', 'K[9,3,3]', 'D[9,3,3]', 'RSI[14]'
            ]
            
            # 匯出為 CSV 檔
            file_name = f"{stock_code}_data.csv"
            file_path = os.path.join(OUTPUT_DIR, file_name)
            
            # 使用 UTF-8 with BOM 存檔，以確保 Excel 可以正確打開中文標頭不亂碼
            df_export.to_csv(file_path, index=False, encoding="utf-8-sig")
            
            print(f" [成功: 成功匯出 -> {file_name}，共 {len(df_export)} 筆]")
            success_count += 1
            
        except Exception as e:
            print(f" [錯誤: {str(e)}，已自動跳過]")
            fail_count += 1
            
        # 微小延遲避免頻繁請求被 yfinance 封鎖
        time.sleep(0.5)

    print("\n==============================================================")
    print(f"[SUCCESS] 執行完畢！成功: {success_count} 檔，失敗: {fail_count} 檔。")
    print(f"[SUCCESS] 資料存放於: {OUTPUT_DIR}")
    print("==============================================================")

if __name__ == "__main__":
    main()
