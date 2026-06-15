# -*- coding: utf-8 -*-
"""
================================================================================
  多指標交叉組合回測搜尋引擎 (Multi-Indicator Backtest Engine)
  
  用途：加載每檔股票過去 900 天的歷史數據，
        透過向量化矩陣運算高速對 128 種指標訊號進行交叉組合回測，
        找出獲利最高且穩健的黃金公式組合，並將排行榜寫入 json。
================================================================================
"""

import os
import glob
import re
import json
import pandas as pd
import numpy as np

# ── 路徑設定 ──
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STOCK_ORIGINAL_DIR = os.path.join(SCRIPT_DIR, "Stock original")
OUTPUT_JSON_PATH = os.path.join(SCRIPT_DIR, "修正版_V5_Server", "public", "leaderboard.json")

def find_column(df, keywords):
    """根據關鍵字模糊匹配 DataFrame 欄位"""
    for col in df.columns:
        for kw in keywords:
            if kw.lower() in str(col).lower():
                return col
    return None

def clean_and_parse_series(df, col_name):
    """清除非數字字元並轉換成 numeric 陣列"""
    if col_name is not None and col_name in df.columns:
        s = df[col_name].astype(str).str.replace(r'[▲▼↑↓△▽,%\s]', '', regex=True)
        return pd.to_numeric(s, errors='coerce').ffill().bfill().fillna(0).values
    return np.zeros(len(df))

def run_simulation(opens, highs, lows, closes, entry_signals, exit_signals, tp, sl):
    """
    執行單次交易模擬
    - 進場：於訊號觸發次日開盤買入 1000 股
    - 出場：達到停利TP、停損SL，或觸發出場訊號
    """
    shares = 1000
    pnl = 0
    trades = 0
    wins = 0
    hold = False
    buy_price = 0
    max_capital = 0
    
    n_days = len(closes)
    for i in range(1, n_days - 1):
        if not hold:
            if entry_signals[i]:
                hold = True
                buy_price = opens[i+1] # 次日開盤買入
                trades += 1
                max_capital = max(max_capital, buy_price * shares)
        else:
            next_open = opens[i+1]
            trade_roi = (next_open - buy_price) / buy_price if buy_price > 0 else 0
            
            # 檢查出場條件
            cond_tp = (tp is not None) and (trade_roi >= tp)
            cond_sl = (sl is not None) and (trade_roi <= -sl)
            cond_signal = exit_signals[i]
            
            if cond_tp or cond_sl or cond_signal:
                hold = False
                sell_price = next_open
                trade_pnl = (sell_price - buy_price) * shares
                pnl += trade_pnl
                if trade_pnl > 0:
                    wins += 1
                buy_price = 0
                
    win_rate = (wins / trades * 100) if trades > 0 else 0
    roi = (pnl / max_capital * 100) if max_capital > 0 else 0
    return pnl, win_rate, trades, max_capital, roi

def main():
    print("=" * 60)
    print("  多指標交叉組合回測搜尋引擎 啟動中...")
    print("=" * 60)

    # 1. 搜尋 Stock original 中的 Excel 檔案
    # 優先找 *_EOM_*.xlsx，若無則找 *.xlsx
    xlsx_files = glob.glob(os.path.join(STOCK_ORIGINAL_DIR, "*_EOM_*.xlsx"))
    if not xlsx_files:
        xlsx_files = glob.glob(os.path.join(STOCK_ORIGINAL_DIR, "*.xlsx"))
    
    # 過濾掉備份子資料夾中的檔案
    xlsx_files = [f for f in xlsx_files if os.path.isfile(f)]

    if not xlsx_files:
        print(f"❌ 在 {STOCK_ORIGINAL_DIR} 找不到任何 Excel 數據檔案！")
        return

    print(f"📁 找到 {len(xlsx_files)} 個個股數據檔案，開始載入與回測分析...")

    leaderboard_data = []

    for file_path in xlsx_files:
        filename = os.path.basename(file_path)
        # 提取代號與名稱 (例如 2330_台積電_EOM_20260615.xlsx -> code=2330, name=台積電)
        base = filename.replace('.xlsx', '')
        parts = base.split('_')
        if len(parts) >= 2:
            code, name = parts[0], parts[1]
        else:
            code, name = base, base

        # 排除非純數字股號的檔案 (例如系統表單、策略說明等)
        if not code.isdigit():
            continue

        try:
            df = pd.read_excel(file_path, header=0)
        except Exception as ex:
            print(f"⚠️ 無法讀取檔案 {filename}: {ex}")
            continue

        # 確保欄位名稱乾淨
        df.columns = [str(c).strip() for c in df.columns]

        # 限制只分析過去 900 天數據
        df = df.tail(900).reset_index(drop=True)
        n_rows = len(df)
        if n_rows < 20:
            print(f"⚠️ 個股 {code} {name} 數據筆數不足 20 筆，跳過")
            continue

        # 2. 匹配並加載所有技術指標欄位
        c_date = find_column(df, ['日', 'Date', 'date'])
        c_open = find_column(df, ['開盤', 'Open', 'open'])
        c_high = find_column(df, ['最高', 'High', 'high'])
        c_low = find_column(df, ['最低', 'Low', 'low'])
        c_close = find_column(df, ['收盤', 'Close', 'close'])
        c_ma5 = find_column(df, ['均價[5]', 'MA5', 'ma5'])
        c_ma20 = find_column(df, ['均價[20]', 'MA20', 'ma20'])
        c_ma60 = find_column(df, ['均價[60]', 'MA60', 'ma60'])
        c_ma120 = find_column(df, ['均價[120]', 'MA120', 'ma120'])
        c_eom = find_column(df, ['EOM[60]', 'EOM'])
        c_eom_sig = find_column(df, ['Signal[20]', 'EOM_Signal'])
        c_mfi = find_column(df, ['MFI[14]', 'MFI'])
        c_macd = find_column(df, ['MACD', 'MACD柱', 'MACD 柱'])
        c_k = find_column(df, ['%KS', 'K(9,3,3)'])
        c_d = find_column(df, ['%DS', 'D(9,3,3)'])
        c_rsi = find_column(df, ['RSI[14]', 'RSI'])
        c_bias5 = find_column(df, ['BIAS[5]', 'BIAS5'])
        c_bias20 = find_column(df, ['BIAS[20]', 'BIAS20'])
        c_cci = find_column(df, ['CCI[20]', 'CCI'])
        c_bb_upper = find_column(df, ['布林加通道 上軌', '布林加通道 上', 'BB_Upper'])
        c_bb_lower = find_column(df, ['布林加通道 下軌', '布林加通道 下', 'BB_Lower'])
        c_pivot = find_column(df, ['Pivot', 'pivot'])
        c_r1 = find_column(df, ['第1道壓力', 'R1'])
        c_s1 = find_column(df, ['第1道支撐', 'S1'])

        # 轉換陣列
        dates = df[c_date].astype(str).values if c_date else np.array([str(i) for i in range(n_rows)])
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
        bias5 = clean_and_parse_series(df, c_bias5)
        bias20 = clean_and_parse_series(df, c_bias20)
        cci = clean_and_parse_series(df, c_cci)
        bb_upper = clean_and_parse_series(df, c_bb_upper)
        bb_lower = clean_and_parse_series(df, c_bb_lower)
        pivot = clean_and_parse_series(df, c_pivot)
        r1 = clean_and_parse_series(df, c_r1)
        s1 = clean_and_parse_series(df, c_s1)

        # 3. 預計算獨立技術訊號 Boolean 陣列
        prev_k = np.roll(k, 1); prev_k[0] = k[0]
        prev_d = np.roll(d, 1); prev_d[0] = d[0]
        prev_macd = np.roll(macd, 1); prev_macd[0] = macd[0]

        # 買入基本訊號
        f_kd_gold = (k > d) & (prev_k <= prev_d)
        f_kd_oversold = k < 30
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

        # 賣出基本訊號
        f_kd_dead = (k < d) & (prev_k >= prev_d)
        f_kd_overbought = k > 70
        f_rsi_overbought = rsi > 65
        f_macd_shrink = macd < prev_macd
        f_below_ma20 = closes < ma20
        f_bb_overbought = (closes > bb_upper) & (bb_upper > 0)
        f_below_s1 = (closes < s1) & (s1 > 0)

        # 4. 定義進場交叉組合策略 (16 種)
        entry_strategies = [
            ("均線多頭+MACD增長", f_ma_bull & f_macd_grow),
            ("站上MA20+MACD紅柱", f_above_ma20 & f_macd_positive),
            ("EOM強勢+站上MA60", f_eom_bullish & f_above_ma60),
            ("RSI多頭+MACD增長", f_rsi_bull & f_macd_grow),
            ("突破樞軸與第一阻力", f_above_pivot & f_break_r1),
            ("站上MA20+均線多頭", f_above_ma20 & f_ma_bull),
            ("KD金叉+KD超賣", f_kd_gold & f_kd_oversold),
            ("RSI超賣+KD金叉", f_rsi_oversold & f_kd_gold),
            ("BIAS超賣+KD金叉", f_bias_oversold & f_kd_gold),
            ("CCI超賣+RSI超賣", f_cci_oversold & f_rsi_oversold),
            ("布林下軌超跌+KD金叉", f_bb_oversold & f_kd_gold),
            ("MFI超賣+BIAS超賣", f_mfi_oversold & f_bias_oversold),
            ("CCI超賣+KD金叉", f_cci_oversold & f_kd_gold),
            ("MFI超賣+KD金叉", f_mfi_oversold & f_kd_gold),
            ("突破阻力(R1)+MACD增長", f_break_r1 & f_macd_grow),
            ("突破阻力(R1)+RSI多頭", f_break_r1 & f_rsi_bull)
        ]

        # 5. 定義出場交叉組合策略 (8 種)
        # tp, sl, exit_signals
        exit_strategies = [
            ("10%停利/5%停損", 0.10, -0.05, np.zeros(n_rows, dtype=bool)),
            ("15%停利/8%停損", 0.15, -0.08, np.zeros(n_rows, dtype=bool)),
            ("KD死叉或5%停損", None, -0.05, f_kd_dead),
            ("RSI超買或5%停損", None, -0.05, f_rsi_overbought),
            ("MACD縮短或5%停損", None, -0.05, f_macd_shrink),
            ("跌破MA20或5%停損", None, -0.05, f_below_ma20),
            ("布林上軌停利或5%停損", None, -0.05, f_bb_overbought),
            ("跌破支撐(S1)或10%停利", 0.10, None, f_below_s1)
        ]

        # 6. 開始進行 16 * 8 = 128 種交叉組合爆破回測
        best_pnl = -99999999
        best_combo_name = "無合適交易"
        best_performance = {"profit": 0, "roi": 0, "winRate": 0, "trades": 0}

        for ent_name, ent_sig in entry_strategies:
            for ext_name, tp, sl, ext_sig in exit_strategies:
                pnl, win_rate, trades, max_cap, roi = run_simulation(
                    opens, highs, lows, closes, ent_sig, ext_sig, tp, sl
                )
                
                # 排除交易次數太少 (低於 3 次) 的無效偏誤策略
                if trades >= 3:
                    if pnl > best_pnl:
                        best_pnl = pnl
                        best_combo_name = f"{ent_name} & {ext_name}"
                        best_performance = {
                            "profit": pnl,
                            "roi": roi,
                            "winRate": win_rate,
                            "trades": trades
                        }

        # 7. 註冊最佳成果
        if best_pnl != -99999999:
            leaderboard_data.append({
                "code": code,
                "name": name,
                "strategy": best_combo_name,
                "profit": best_performance["profit"],
                "roi": best_performance["roi"],
                "winRate": best_performance["winRate"],
                "trades": best_performance["trades"]
            })
            print(f"  ✅ {code} {name:4s} | 最佳策略：{best_combo_name:<25s} | 獲利：{best_performance['profit']:+10,.0f} 元 | 勝率：{best_performance['winRate']:5.1f}% | ROI：{best_performance['roi']:5.1f}%")
        else:
            print(f"  ⚠️ {code} {name:4s} | 無符合最低交易頻率之最佳策略")

    # 8. 儲存至 JSON 排行榜
    if leaderboard_data:
        # 按照 Profit (盈虧) 由大到小排序
        leaderboard_data.sort(key=lambda x: x["profit"], reverse=True)
        os.makedirs(os.path.dirname(OUTPUT_JSON_PATH), exist_ok=True)
        with open(OUTPUT_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(leaderboard_data, f, indent=4, ensure_ascii=False)
        print(f"\n🎉 搜尋完畢！最佳交叉組合策略排行已成功寫入：{OUTPUT_JSON_PATH}")
    else:
        print("\n❌ 未能產出任何有效的回測組合排行數據。")

if __name__ == "__main__":
    main()
