# -*- coding: utf-8 -*-
"""
================================================================================
  75%勝率矩陣策略篩選引擎 (75% Win Rate Matrix Search Engine)
  
  用途：以極速 pandas 載入 auto_export 中的所有個股數據，
        透過 180 種指標交叉組合進行爆破回測，
        嚴格篩選出勝率 >= 75% 且交易次數 >= 5 次的個股與策略組合，
        將結果排序後寫入 leaderboard.json，並作為新版高勝率推薦清單。
================================================================================
"""

import os
import glob
import json
import pandas as pd
import numpy as np

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.int64, np.int32, np.int16, np.int8)):
            return int(obj)
        elif isinstance(obj, (np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

# ── 路徑設定 ──
SCRIPT_DIR = r"E:\G-AI-1\Stock analysis"
STOCK_ORIGINAL_DIR = os.path.join(SCRIPT_DIR, "Stock original")
AUTO_EXPORT_DIR = os.path.join(STOCK_ORIGINAL_DIR, "auto_export")
OUTPUT_JSON_PATH = os.path.join(SCRIPT_DIR, "修正版_V6_Server", "public", "leaderboard.json")

def find_column(df, keywords):
    for col in df.columns:
        for kw in keywords:
            if kw.lower() in str(col).lower():
                return col
    return None

def clean_and_parse_series(df, col_name):
    if col_name is not None and col_name in df.columns:
        s = df[col_name].astype(str).str.replace(r'[▲▼↑↓△▽,%\s]', '', regex=True)
        return pd.to_numeric(s, errors='coerce').ffill().bfill().fillna(0).values
    return np.zeros(len(df))

def main():
    print("=" * 60)
    print("  [Start] 75% Win Rate Matrix Search Engine starting...")
    print("=" * 60)

    # 1. 搜尋所有個股 Excel 檔案
    candidate_files = []
    for folder in [AUTO_EXPORT_DIR, STOCK_ORIGINAL_DIR]:
        if os.path.exists(folder):
            candidate_files.extend(glob.glob(os.path.join(folder, "*.xlsx")))
            candidate_files.extend(glob.glob(os.path.join(folder, "*.xls")))
            candidate_files.extend(glob.glob(os.path.join(folder, "*.csv")))

    # 按股號分組，只保留日期最新的檔案
    stock_files_map = {}
    for f in candidate_files:
        filename = os.path.basename(f)
        base = os.path.splitext(filename)[0]
        parts = base.split('_')
        code = parts[0]
        date_str = parts[-1] if len(parts) >= 3 else ""
        if code not in stock_files_map or date_str > stock_files_map[code][1]:
            stock_files_map[code] = (f, date_str)

    selected_files = [v[0] for v in stock_files_map.values()]
    total_files = len(selected_files)
    print(f"[Info] Found {total_files} unique stock files, starting search...")

    leaderboard_data = []

    # 2. 定義進出場策略名稱 (供對照使用)
    entry_strategies_names = [
        "強勢均線多頭+KD金叉", "中長期多頭+RSI低檔轉強", "雙重均線突破+MACD翻紅", 
        "EOM動能突破+均線多頭", "極度超跌共振 (BIAS+RSI+MFI)", "布林通道下軌+KD低檔金叉", 
        "CCI超賣+MFI超賣+KD金叉", "雙重超賣 (RSI+CCI)+MACD轉強", "樞軸點(S1)支撐+KD金叉", 
        "突破阻力(R1)+MACD多頭", "突破樞軸(Pivot)+RSI轉強", "S1支撐不破+MACD紅柱增長", 
        "多頭拉回：MA60之上+KD金叉+RSI<45", "布林中軌支撐+MACD紅柱", "動能共振：EOM突破+MACD>0+RSI>50", 
        "雙保險超跌：BIAS超賣+布林下軌觸及", "主力資金流入：MFI超賣+EOM突破", "壓力突破：價格>R1+EOM強勢+MACD>0", 
        "長期均線支撐：站上MA120+KD金叉+CCI超賣", "CCI超賣反彈+MACD紅柱增長"
    ]

    exit_strategies_names = [
        "6%停利 / 6%停損 (穩健勝率)", "8%停利 / 8%停損 (均衡配置)", "12%停利 / 6%停損 (高盈虧比)",
        "KD死叉離場或6%停損", "RSI超買離場或6%停損", "MACD紅柱縮短離場或6%停損",
        "收盤跌破MA20或6%停損", "觸碰布林上軌停利或6%停損", "跌破樞軸支撐(S1)或8%停利"
    ]

    processed_count = 0
    success_count = 0

    for filepath in selected_files:
        filename = os.path.basename(filepath)
        base = os.path.splitext(filename)[0]
        parts = base.split('_')
        if len(parts) < 2 or not parts[0].isdigit():
            continue
        code, name = parts[0], parts[1]
        processed_count += 1

        # 讀取 Excel 
        try:
            if filepath.endswith('.csv'):
                try:
                    df = pd.read_csv(filepath, encoding='cp950', header=0)
                except:
                    df = pd.read_csv(filepath, encoding='utf-8', header=0)
            else:
                try:
                    df = pd.read_excel(filepath, sheet_name=1, header=7)
                except:
                    df = pd.read_excel(filepath, sheet_name=0, header=0)
        except Exception:
            continue

        df.columns = [str(c).strip() for c in df.columns]
        
        # 限制只分析最後 900 天數據
        df = df.tail(900).reset_index(drop=True)
        n_rows = len(df)
        if n_rows < 20:
            continue

        # 模糊匹配技術指標欄位
        c_open = find_column(df, ['開盤價', '開盤', 'Open', 'open'])
        c_high = find_column(df, ['最高價', '最高', 'High', 'high'])
        c_low = find_column(df, ['最低價', '最低', 'Low', 'low'])
        c_close = find_column(df, ['收盤價', '收盤', 'Close', 'close'])
        c_ma5 = find_column(df, ['均價[5]', 'MA5', 'ma5'])
        c_ma20 = find_column(df, ['均價[20]', 'MA20', 'ma20'])
        c_ma60 = find_column(df, ['均價[60]', 'MA60', 'ma60'])
        c_ma120 = find_column(df, ['均價[120]', 'MA120', 'ma120'])
        c_eom = find_column(df, ['EOM[60]', 'EOM'])
        c_eom_sig = find_column(df, ['Signal[20]', 'EOM_Signal'])
        c_mfi = find_column(df, ['MFI[14]', 'MFI'])
        c_macd = find_column(df, ['MACD', 'MACD柱', 'MACD 柱', 'MACD 柱狀體'])
        c_k = find_column(df, ['%KS', 'K(9,3,3)', 'K值'])
        c_d = find_column(df, ['%DS', 'D(9,3,3)', 'D值'])
        c_rsi = find_column(df, ['RSI[14]', 'RSI'])
        c_bias20 = find_column(df, ['BIAS[20]', 'BIAS20'])
        c_cci = find_column(df, ['CCI[20]', 'CCI'])
        c_bb_upper = find_column(df, ['布林加通道 上軌', 'BB_Upper'])
        c_bb_lower = find_column(df, ['布林加通道 下軌', 'BB_Lower'])
        c_pivot = find_column(df, ['Pivot', 'pivot'])
        c_r1 = find_column(df, ['第1道壓力', 'R1'])
        c_s1 = find_column(df, ['第1道支撐', 'S1'])

        # 轉換陣列
        opens = clean_and_parse_series(df, c_open)
        highs = clean_and_parse_series(df, c_high)
        lows = clean_and_parse_series(df, c_low)
        closes = clean_and_parse_series(df, c_close)
        ma5 = clean_and_parse_series(df, c_ma5)
        ma20 = clean_and_parse_series(df, c_ma20)
        ma60 = clean_and_parse_series(df, c_ma60)
        ma120 = clean_and_parse_series(df, c_ma120)
        eom = clean_and_parse_series(df, c_eom)
        eom_sig = clean_and_parse_series(df, c_eom_sig)
        mfi = clean_and_parse_series(df, c_mfi)
        macd = clean_and_parse_series(df, c_macd)
        k = clean_and_parse_series(df, c_k)
        d = clean_and_parse_series(df, c_d)
        rsi = clean_and_parse_series(df, c_rsi)
        bias20 = clean_and_parse_series(df, c_bias20)
        cci = clean_and_parse_series(df, c_cci)
        bb_upper = clean_and_parse_series(df, c_bb_upper)
        bb_lower = clean_and_parse_series(df, c_bb_lower)
        pivot = clean_and_parse_series(df, c_pivot)
        r1 = clean_and_parse_series(df, c_r1)
        s1 = clean_and_parse_series(df, c_s1)

        prev_k = np.roll(k, 1); prev_k[0] = k[0]
        prev_d = np.roll(d, 1); prev_d[0] = d[0]
        prev_macd = np.roll(macd, 1); prev_macd[0] = macd[0]

        # 買入訊號
        f_kd_gold = (k > d) & (prev_k <= prev_d)
        f_rsi_oversold = rsi < 35
        f_rsi_bull = rsi > 50
        f_macd_grow = macd > prev_macd
        f_macd_positive = macd > 0
        f_bias_oversold = bias20 < -4
        f_cci_oversold = cci < -100
        f_eom_bullish = eom > eom_sig
        f_mfi_oversold = mfi < 30
        f_bb_oversold = (closes < bb_lower) & (bb_lower > 0)
        f_above_pivot = closes > pivot
        f_break_r1 = (closes > r1) & (r1 > 0)
        f_ma_bull = (ma5 > ma20) & (ma20 > ma60)
        f_above_ma20 = closes > ma20
        f_above_ma60 = closes > ma60
        f_above_ma120 = closes > ma120

        # 賣出訊號
        f_kd_dead = (k < d) & (prev_k >= prev_d)
        f_rsi_overbought = rsi > 65
        f_macd_shrink = macd < prev_macd
        f_below_ma20 = closes < ma20
        f_bb_overbought = (closes > bb_upper) & (bb_upper > 0)
        f_below_s1 = (closes < s1) & (s1 > 0)

        c_low_col = find_column(df, ['最低價', '最低', 'Low', 'low'])
        low_vals = df[c_low_col].values if c_low_col else lows

        entry_strategies = [
            ("強勢均線多頭+KD金叉", f_ma_bull & f_kd_gold & f_above_ma20),
            ("中長期多頭+RSI低檔轉強", f_above_ma60 & f_above_ma120 & (rsi < 45) & f_macd_grow),
            ("雙重均線突破+MACD翻紅", f_above_ma20 & f_above_ma60 & f_macd_positive & f_macd_grow),
            ("EOM動能突破+均線多頭", f_eom_bullish & f_ma_bull & f_above_ma20),
            ("極度超跌共振 (BIAS+RSI+MFI)", f_bias_oversold & f_rsi_oversold & f_mfi_oversold),
            ("布林通道下軌+KD低檔金叉", f_bb_oversold & f_kd_gold),
            ("CCI超賣+MFI超賣+KD金叉", f_cci_oversold & f_mfi_oversold & f_kd_gold),
            ("雙重超賣 (RSI+CCI)+MACD轉強", f_rsi_oversold & f_cci_oversold & f_macd_grow),
            ("樞軸點(S1)支撐+KD金叉", (closes > s1) & (low_vals <= s1) & f_kd_gold & (s1 > 0)),
            ("突破阻力(R1)+MACD多頭", f_break_r1 & f_macd_positive & f_above_ma20),
            ("突破樞軸(Pivot)+RSI轉強", f_above_pivot & f_rsi_bull & f_macd_grow),
            ("S1支撐不破+MACD紅柱增長", (closes > s1) & f_macd_grow & (s1 > 0)),
            ("多頭拉回：MA60之上+KD金叉+RSI<45", f_above_ma60 & f_kd_gold & (rsi < 45)),
            ("布林中軌支撐+MACD紅柱", (closes > bb_lower) & (closes < bb_upper) & f_above_ma20 & f_macd_grow),
            ("動能共振：EOM突破+MACD>0+RSI>50", f_eom_bullish & f_macd_positive & f_rsi_bull),
            ("雙保險超跌：BIAS超賣+布林下軌觸及", f_bias_oversold & f_bb_oversold),
            ("主力資金流入：MFI超賣+EOM突破", f_mfi_oversold & f_eom_bullish),
            ("壓力突破：價格>R1+EOM強勢+MACD>0", f_break_r1 & f_eom_bullish & f_macd_positive),
            ("長期均線支撐：站上MA120+KD金叉+CCI超賣", f_above_ma120 & f_kd_gold & f_cci_oversold),
            ("CCI超賣反彈+MACD紅柱增長", f_cci_oversold & f_macd_grow & f_above_ma20)
        ]

        exit_strategies = [
            ("6%停利 / 6%停損 (穩健勝率)", 0.06, 0.06, np.zeros(n_rows, dtype=bool)),
            ("8%停利 / 8%停損 (均衡配置)", 0.08, 0.08, np.zeros(n_rows, dtype=bool)),
            ("12%停利 / 6%停損 (高盈虧比)", 0.12, 0.06, np.zeros(n_rows, dtype=bool)),
            ("KD死叉離場或6%停損", None, 0.06, f_kd_dead),
            ("RSI超買離場或6%停損", None, 0.06, f_rsi_overbought),
            ("MACD紅柱縮短離場或6%停損", None, 0.06, f_macd_shrink),
            ("收盤跌破MA20或6%停損", None, 0.06, f_below_ma20),
            ("觸碰布林上軌停利或6%停損", None, 0.06, f_bb_overbought),
            ("跌破樞軸支撐(S1)或8%停利", 0.08, None, f_below_s1)
        ]

        best_combo_name = None
        best_pnl = -99999999
        best_win_rate = 0.0
        best_trades = 0
        best_roi = 0.0
        best_hold = False
        best_buy_price = 0.0
        best_buy_date = None
        best_current_price = 0.0

        # 執行 180 種組合回測
        for ent_name, ent_sig in entry_strategies:
            for ext_name, tp, sl, ext_sig in exit_strategies:
                shares = 1000
                pnl = 0
                trades = 0
                wins = 0
                hold = False
                buy_price = 0
                buy_date = None
                max_capital = 0

                for i in range(1, n_rows - 1):
                    if not hold:
                        if ent_sig[i]:
                            hold = True
                            buy_price = opens[i+1]
                            try:
                                buy_date = str(int(float(df.iloc[i+1, 0])))
                            except Exception:
                                buy_date = str(df.iloc[i+1, 0]).strip()
                            trades += 1
                            max_capital = max(max_capital, buy_price * shares)
                    else:
                        next_open = opens[i+1]
                        trade_roi = (next_open - buy_price) / buy_price if buy_price > 0 else 0
                        
                        cond_tp = (tp is not None) and (trade_roi >= tp)
                        cond_sl = (sl is not None) and (trade_roi <= -sl)
                        cond_signal = ext_sig[i]

                        if cond_tp or cond_sl or cond_signal:
                            hold = False
                            sell_price = next_open
                            trade_pnl = (sell_price - buy_price) * shares
                            pnl += trade_pnl
                            if trade_pnl > 0:
                                wins += 1
                            buy_price = 0
                            buy_date = None

                win_rate = (wins / trades * 100) if trades > 0 else 0
                roi = (pnl / max_capital * 100) if max_capital > 0 else 0

                # 條件：交易次數 >= 5 且勝率 >= 75% 且整體 ROI >= 60.0% 且利潤高於目前最優
                if trades >= 5 and win_rate >= 75.0 and roi >= 60.0:
                    if pnl > best_pnl:
                        best_pnl = pnl
                        best_win_rate = win_rate
                        best_trades = trades
                        best_roi = roi
                        best_combo_name = f"{ent_name} & {ext_name}"
                        # 紀錄最新持倉狀態
                        best_hold = hold
                        best_buy_price = buy_price
                        best_buy_date = buy_date
                        best_current_price = closes[-1] if len(closes) > 0 else 0

        # 註冊篩選結果
        if best_combo_name is not None:
            success_count += 1
            holding_obj = None
            if best_hold:
                holding_pnl = (best_current_price - best_buy_price) * 1000
                holding_roi = ((best_current_price - best_buy_price) / best_buy_price * 100) if best_buy_price > 0 else 0
                holding_obj = {
                    "hold": True,
                    "buyDate": best_buy_date,
                    "buyPrice": best_buy_price,
                    "currentPrice": best_current_price,
                    "pnl": holding_pnl,
                    "roi": holding_roi,
                    "shares": 1.0,
                    "posType": "多單"
                }

            leaderboard_data.append({
                "code": code,
                "name": name,
                "strategy": best_combo_name,
                "profit": best_pnl,
                "roi": best_roi,
                "winRate": best_win_rate,
                "trades": best_trades,
                "holding": holding_obj
            })
            print(f"  [SUCCESS {success_count}] {code} {name:4s} | WinRate: {best_win_rate:5.1f}% | Profit: {best_pnl:+10,.0f} | Trades: {best_trades:3d} | Strategy: {best_combo_name} | Holding: {best_hold}")

        if processed_count % 50 == 0:
            print(f"[Progress] Processed {processed_count}/{total_files} stocks...")

    # 寫入排行榜並存檔
    if leaderboard_data:
        leaderboard_data.sort(key=lambda x: x["profit"], reverse=True)
        os.makedirs(os.path.dirname(OUTPUT_JSON_PATH), exist_ok=True)
        with open(OUTPUT_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(leaderboard_data, f, indent=4, ensure_ascii=False, cls=NumpyEncoder)
        print(f"\n[Done] Search finished! Found {success_count} stocks with win rate >= 75%!")
        print(f"Leaderboard written to {OUTPUT_JSON_PATH}")
    else:
        print("\n[Warning] No stock strategy combination achieved win rate >= 75% and trades >= 5!")

if __name__ == "__main__":
    main()
