# -*- coding: utf-8 -*-
"""
================================================================================
  V8.2 雙向（多單/空單）75%勝率策略回測引擎 (75% Win Rate Matrix Search Engine V8.2)
  
  用途：以極速 pandas/numpy 載入 auto_export 中的個股數據，
        各自獨立執行 225 種多單與 225 種空單策略組合之矩陣回測，
        新增 10 種自適應多尺度「型態」（W底、M頭、頭肩、V反轉、三角、箱型）趨勢整理策略，
        嚴格篩選出勝率 >= 75% 且交易次數 >= 5、整體 ROI >= 60.0% 的最佳組合，
        將結果寫入 leaderboard_v8_2.json，並將所有成交明細寫入 trades_v8_2.json。
================================================================================
"""

import os
import glob
import json
import pandas as pd
import numpy as np
import re

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
OUTPUT_LEADERBOARD_PATH = os.path.join(SCRIPT_DIR, "修正版_V6_Server", "public", "leaderboard_v8_2.json")
OUTPUT_TRADES_PATH = os.path.join(SCRIPT_DIR, "修正版_V6_Server", "public", "trades_v8_2.json")

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
    print("  [Start] 75% Win Rate Matrix Search Engine V8.2 starting...")
    print("=" * 60)

    # 1. 搜尋所有個股 Excel/CSV 檔案
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
        # 排除已生成的 AI 回測 Excel 檔
        if "AI" in filename or "V4" in filename or "V_Rebound" in filename or "V_Dip" in filename:
            continue
        if code not in stock_files_map or date_str > stock_files_map[code][1]:
            stock_files_map[code] = (f, date_str)

    selected_files = [v[0] for v in stock_files_map.values()]
    total_files = len(selected_files)
    print(f"[Info] Found {total_files} unique stock files, starting search...")

    leaderboard_data = []
    trade_cycles_log = []

    # ── 策略名稱定義 (新增 5 個多單型態與 5 個空單型態) ──
    long_entry_names = [
        "強勢均線多頭+KD金叉", "中長期多頭+RSI低檔轉強", "雙重均線突破+MACD翻紅", 
        "EOM動能突破+均線多頭", "極度超跌共振 (BIAS+RSI+MFI)", "布林通道下軌+KD低檔金叉", 
        "CCI超賣+MFI超賣+KD金叉", "雙重超賣 (RSI+CCI)+MACD轉強", "樞軸點(S1)支撐+KD金叉", 
        "突破阻力(R1)+MACD多頭", "突破樞軸(Pivot)+RSI轉強", "S1支撐不破+MACD紅柱增長", 
        "多頭拉回：MA60之上+KD金叉+RSI<45", "布林中軌支撐+MACD紅柱", "動能共振：EOM突破+MACD>0+RSI>50", 
        "雙保險超跌：BIAS超賣+布林下軌觸及", "主力資金流入：MFI超賣+EOM突破", "壓力突破：價格>R1+EOM強勢+MACD>0", 
        "長期均線支撐：站上MA120+KD金叉+CCI超賣", "CCI超賣反彈+MACD紅柱增長",
        "W底雙重底突破頸線 (多頭趨勢)", "頭肩底突破頸線確立 (多頭趨勢)", "V型反轉爆量向上拉升 (多頭趨勢)",
        "三角收斂突破上軌加速 (多頭整理)", "箱型整理突破阻力上限 (多頭整理)"
    ]
    long_exit_names = [
        "6%停利 / 6%停損 (穩健勝率)", "8%停利 / 8%停損 (均衡配置)", "12%停利 / 6%停損 (高盈虧比)",
        "KD死叉離場或6%停損", "RSI超買離場或6%停損", "MACD紅柱縮短離場或6%停損",
        "收盤跌破MA20或6%停損", "觸碰布林上軌停利或6%停損", "跌破樞軸支撐(S1)或8%停利"
    ]

    short_entry_names = [
        "弱勢均線空頭+KD死叉", "中長期空頭+RSI高檔轉弱", "雙重均線跌破+MACD翻綠", 
        "EOM動能下跌+均線空頭", "極度超買共振 (BIAS+RSI+MFI)", "布林通道上軌+KD高檔死叉", 
        "CCI超買+MFI超買+KD死叉", "雙重超買 (RSI+CCI)+MACD轉弱", "樞軸點(R1)壓力+KD死叉", 
        "跌破支撐(S1)+MACD空頭", "跌破樞軸(Pivot)+RSI轉弱", "R1壓力不破+MACD綠柱增長", 
        "空頭拉回：MA60之下+KD死叉+RSI>55", "布林中軌阻力+MACD綠柱", "動能共振：EOM下跌+MACD<0+RSI<50", 
        "雙保險超買：BIAS超買+布林上軌觸及", "主力資金流出：MFI超買+EOM下跌", "支撐跌破：價格<S1+EOM弱勢+MACD<0", 
        "長期均線阻力：跌破MA120+KD死叉+CCI超買", "CCI超買回檔+MACD綠柱增長",
        "M頭雙重頂跌破頸線 (空頭趨勢)", "頭肩頂跌破頸線反轉 (空頭趨勢)", "倒V型反轉急速暴跌 (空頭趨勢)",
        "三角收斂跌破下軌加速 (空頭整理)", "箱型整理跌破支撐下限 (空頭整理)"
    ]
    short_exit_names = [
        "6%停利 / 6%停損 (穩健勝率)", "8%停利 / 8%停損 (均衡配置)", "12%停利 / 6%停損 (高盈虧比)",
        "KD金叉離場或6%停損", "RSI超賣離場或6%停損", "MACD綠柱縮短離場或6%停損",
        "收盤站上MA20或6%停損", "觸碰布林下軌停利或6%停損", "突破壓力(R1)或8%停利"
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

        # 讀取 Excel/CSV
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
        df = df.tail(900).reset_index(drop=True)
        n_rows = len(df)
        if n_rows < 20:
            continue

        # 匹配技術指標欄位
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

        # ── 多單（Long）指標條件 ──
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

        # ── 空單（Short）指標條件 ──
        f_kd_dead = (k < d) & (prev_k >= prev_d)
        f_rsi_overbought = rsi > 65
        f_macd_shrink = macd < prev_macd
        f_below_ma20 = closes < ma20
        f_bb_overbought = (closes > bb_upper) & (bb_upper > 0)
        f_below_s1 = (closes < s1) & (s1 > 0)

        c_low_col = find_column(df, ['最低價', '最低', 'Low', 'low'])
        low_vals = df[c_low_col].values if c_low_col else lows
        c_high_col = find_column(df, ['最高價', '最高', 'High', 'high'])
        high_vals = df[c_high_col].values if c_high_col else highs

        # ── 自適應多尺度「型態」運算 (V8.2 新增) ──
        f_w_bottom = np.zeros(n_rows, dtype=bool)
        f_hs_bottom = np.zeros(n_rows, dtype=bool)
        f_v_rebound = np.zeros(n_rows, dtype=bool)
        f_triangle_breakout = np.zeros(n_rows, dtype=bool)
        f_box_breakout = np.zeros(n_rows, dtype=bool)

        f_m_top = np.zeros(n_rows, dtype=bool)
        f_hs_top = np.zeros(n_rows, dtype=bool)
        f_inverted_v = np.zeros(n_rows, dtype=bool)
        f_triangle_breakdown = np.zeros(n_rows, dtype=bool)
        f_box_breakdown = np.zeros(n_rows, dtype=bool)

        for S in [15, 30, 60]:
            if n_rows < S + 5:
                continue
            
            # W底 (雙重底)
            v1_idx_shift = S
            v1_len = max(5, int(S * 0.6))
            v2_idx_shift = 2
            v2_len = max(4, int(S * 0.4))
            peak_len = max(4, int(S * 0.4))
            
            min1 = pd.Series(lows).shift(v1_idx_shift).rolling(v1_len).min().values
            min2 = pd.Series(lows).shift(v2_idx_shift).rolling(v2_len).min().values
            peak = pd.Series(highs).shift(v2_len).rolling(peak_len).max().values
            
            c_w_base = (np.abs(min1 - min2) / (min1 + 1e-5) < 0.03) & (peak > min1)
            c_w_break = (closes > peak) & (np.roll(closes, 1) <= peak)
            f_w_bottom = f_w_bottom | (c_w_base & c_w_break)
            
            # 頭肩底
            s_div = max(3, int(S / 3))
            v1_hs = pd.Series(lows).shift(s_div * 2).rolling(s_div).min().values
            v2_hs = pd.Series(lows).shift(s_div).rolling(s_div).min().values
            v3_hs = pd.Series(lows).shift(2).rolling(s_div).min().values
            peak_hs = pd.Series(highs).shift(2).rolling(S).max().values
            
            c_hs_base = (v2_hs < v1_hs) & (v2_hs < v3_hs) & (np.abs(v1_hs - v3_hs) / (v1_hs + 1e-5) < 0.04)
            c_hs_break = (closes > peak_hs) & (np.roll(closes, 1) <= peak_hs)
            f_hs_bottom = f_hs_bottom | (c_hs_base & c_hs_break)

            # V型反轉 (短線急跌後爆量彈升)
            fall_len = max(4, int(S * 0.7))
            rise_len = max(3, int(S * 0.3))
            fall_steep = pd.Series(closes).shift(rise_len).pct_change(fall_len).values < -0.12
            rise_sharp = pd.Series(closes).pct_change(rise_len).values > 0.08
            f_v_rebound = f_v_rebound | (fall_steep & rise_sharp)

            # 三角收斂
            range_S = pd.Series(highs - lows).rolling(S).mean().values
            range_prev = pd.Series(highs - lows).shift(S).rolling(S).mean().values
            volatility_shrink = range_S < (range_prev * 0.7)
            bound_upper = pd.Series(highs).shift(1).rolling(S).max().values
            bound_lower = pd.Series(lows).shift(1).rolling(S).min().values
            f_triangle_breakout = f_triangle_breakout | (volatility_shrink & (closes > bound_upper))
            f_triangle_breakdown = f_triangle_breakdown | (volatility_shrink & (closes < bound_lower))

            # 箱型整理 (矩形)
            box_high = pd.Series(highs).shift(1).rolling(S).max().values
            box_low = pd.Series(lows).shift(1).rolling(S).min().values
            box_range_tight = (box_high - box_low) / (box_low + 1e-5) < 0.06
            f_box_breakout = f_box_breakout | (box_range_tight & (closes > box_high))
            f_box_breakdown = f_box_breakdown | (box_range_tight & (closes < box_low))

            # M頭 (雙重頂)
            max1 = pd.Series(highs).shift(v1_idx_shift).rolling(v1_len).max().values
            max2 = pd.Series(highs).shift(v2_idx_shift).rolling(v2_len).max().values
            valley = pd.Series(lows).shift(v2_len).rolling(peak_len).min().values
            c_m_base = (np.abs(max1 - max2) / (max1 + 1e-5) < 0.03) & (valley < max1)
            c_m_break = (closes < valley) & (np.roll(closes, 1) >= valley)
            f_m_top = f_m_top | (c_m_base & c_m_break)

            # 頭肩頂
            p1_hs = pd.Series(highs).shift(s_div * 2).rolling(s_div).max().values
            p2_hs = pd.Series(highs).shift(s_div).rolling(s_div).max().values
            p3_hs = pd.Series(highs).shift(2).rolling(s_div).max().values
            valley_hs = pd.Series(lows).shift(2).rolling(S).min().values
            c_hst_base = (p2_hs > p1_hs) & (p2_hs > p3_hs) & (np.abs(p1_hs - p3_hs) / (p1_hs + 1e-5) < 0.04)
            c_hst_break = (closes < valley_hs) & (np.roll(closes, 1) >= valley_hs)
            f_hs_top = f_hs_top | (c_hst_base & c_hst_break)

            # 倒V型反轉 (急漲後下殺)
            rise_steep = pd.Series(closes).shift(rise_len).pct_change(fall_len).values > 0.12
            fall_sharp = pd.Series(closes).pct_change(rise_len).values < -0.08
            f_inverted_v = f_inverted_v | (rise_steep & fall_sharp)

        # ── 多單（Long）策略池 ──
        long_entries = [
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
            ("CCI超賣反彈+MACD紅柱增長", f_cci_oversold & f_macd_grow & f_above_ma20),
            # V8.2 新增型態策略
            ("W底雙重底突破頸線 (多頭趨勢)", f_w_bottom),
            ("頭肩底突破頸線確立 (多頭趨勢)", f_hs_bottom),
            ("V型反轉爆量向上拉升 (多頭趨勢)", f_v_rebound),
            ("三角收斂突破上軌加速 (多頭整理)", f_triangle_breakout),
            ("箱型整理突破阻力上限 (多頭整理)", f_box_breakout)
        ]
        long_exits = [
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

        # ── 空單（Short）策略平倉與方向條件 ──
        f_ma_bear = (ma5 < ma20) & (ma20 < ma60)
        f_below_pivot = closes < pivot
        f_break_s1 = (closes < s1) & (s1 > 0)
        f_bias_overbought = bias20 > 4
        f_cci_overbought = cci > 100
        f_eom_bearish = eom < eom_sig
        f_mfi_overbought = mfi > 70
        f_bb_overbought_short = (closes > bb_upper) & (bb_upper > 0)
        f_below_ma60 = closes < ma60
        f_below_ma120 = closes < ma120

        f_kd_gold_cover = f_kd_gold
        f_rsi_oversold_cover = rsi < 35
        f_macd_grow_cover = f_macd_grow
        f_above_ma20_cover = closes > ma20
        f_bb_oversold_cover = (closes < bb_lower) & (bb_lower > 0)
        f_above_r1_cover = (closes > r1) & (r1 > 0)

        short_entries = [
            ("弱勢均線空頭+KD死叉", f_ma_bear & f_kd_dead & f_below_ma20),
            ("中長期空頭+RSI高檔轉弱", f_below_ma60 & f_below_ma120 & (rsi > 55) & f_macd_shrink),
            ("雙重均線跌破+MACD翻綠", f_below_ma20 & f_below_ma60 & (macd < 0) & f_macd_shrink),
            ("EOM動能下跌+均線空頭", f_eom_bearish & f_ma_bear & f_below_ma20),
            ("極度超買共振 (BIAS+RSI+MFI)", f_bias_overbought & f_rsi_overbought & f_mfi_overbought),
            ("布林通道上軌+KD高檔死叉", f_bb_overbought_short & f_kd_dead),
            ("CCI超買+MFI超買+KD死叉", f_cci_overbought & f_mfi_overbought & f_kd_dead),
            ("雙重超買 (RSI+CCI)+MACD轉弱", f_rsi_overbought & f_cci_overbought & f_macd_shrink),
            ("樞軸點(R1)壓力+KD死叉", (closes < r1) & (high_vals >= r1) & f_kd_dead & (r1 > 0)),
            ("跌破支撐(S1)+MACD空頭", f_break_s1 & (macd < 0) & f_below_ma20),
            ("跌破樞軸(Pivot)+RSI轉弱", f_below_pivot & (rsi < 50) & f_macd_shrink),
            ("R1壓力不破+MACD綠柱增長", (closes < r1) & f_macd_shrink & (r1 > 0)),
            ("空頭拉回：MA60之下+KD死叉+RSI>55", f_below_ma60 & f_kd_dead & (rsi > 55)),
            ("布林中軌阻力+MACD綠柱", (closes > bb_lower) & (closes < bb_upper) & f_below_ma20 & f_macd_shrink),
            ("動能共振：EOM下跌+MACD<0+RSI<50", f_eom_bearish & (macd < 0) & (rsi < 50)),
            ("雙保險超買：BIAS超買+布林上軌觸及", f_bias_overbought & f_bb_overbought_short),
            ("主力資金流出：MFI超買+EOM下跌", f_mfi_overbought & f_eom_bearish),
            ("支撐跌破：價格<S1+EOM弱勢+MACD<0", f_break_s1 & f_eom_bearish & (macd < 0)),
            ("長期均線阻力：跌破MA120+KD死叉+CCI超買", (closes < ma120) & f_kd_dead & f_cci_overbought),
            ("CCI超買回檔+MACD綠柱增長", f_cci_overbought & f_macd_shrink & f_below_ma20),
            # V8.2 新增型態策略
            ("M頭雙重頂跌破頸線 (空頭趨勢)", f_m_top),
            ("頭肩頂跌破頸線反轉 (空頭趨勢)", f_hs_top),
            ("倒V型反轉急速暴跌 (空頭趨勢)", f_inverted_v),
            ("三角收斂跌破下軌加速 (空頭整理)", f_triangle_breakdown),
            ("箱型整理跌破支撐下限 (空頭整理)", f_box_breakdown)
        ]
        short_exits = [
            ("6%停利 / 6%停損 (穩健勝率)", 0.06, 0.06, np.zeros(n_rows, dtype=bool)),
            ("8%停利 / 8%停損 (均衡配置)", 0.08, 0.08, np.zeros(n_rows, dtype=bool)),
            ("12%停利 / 6%停損 (高盈虧比)", 0.12, 0.06, np.zeros(n_rows, dtype=bool)),
            ("KD金叉離場或6%停損", None, 0.06, f_kd_gold_cover),
            ("RSI超賣離場或6%停損", None, 0.06, f_rsi_oversold_cover),
            ("MACD綠柱縮短離場或6%停損", None, 0.06, f_macd_grow_cover),
            ("收盤站上MA20或6%停損", None, 0.06, f_above_ma20_cover),
            ("觸碰布林下軌停利或6%停損", None, 0.06, f_bb_oversold_cover),
            ("突破壓力(R1)或8%停利", 0.08, None, f_above_r1_cover)
        ]

        # ── 1. 多單最佳策略矩陣回測 ──
        best_long_combo = None
        best_long_pnl = -99999999
        best_long_win_rate = 0.0
        best_long_trades = 0
        best_long_roi = 0.0
        best_long_hold = False
        best_long_buy_price = 0.0
        best_long_buy_date = None
        best_long_current_price = 0.0
        best_long_trades_list = []

        for ent_name, ent_sig in long_entries:
            for ext_name, tp, sl, ext_sig in long_exits:
                shares = 1000
                pnl = 0
                trades = 0
                wins = 0
                hold = False
                buy_price = 0
                buy_date = None
                max_capital = 0
                temp_trades = []

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
                            
                            try:
                                exit_date = str(int(float(df.iloc[i+1, 0])))
                            except Exception:
                                exit_date = str(df.iloc[i+1, 0]).strip()

                            temp_trades.append({
                                "code": code,
                                "name": name,
                                "type": "long",
                                "strategy": f"{ent_name} & {ext_name}",
                                "posType": "多單",
                                "entryDate": buy_date,
                                "entryPrice": buy_price,
                                "exitDate": exit_date,
                                "exitPrice": sell_price,
                                "pnl": trade_pnl,
                                "roi": trade_roi * 100
                            })
                            buy_price = 0
                            buy_date = None

                win_rate = (wins / trades * 100) if trades > 0 else 0
                roi = (pnl / max_capital * 100) if max_capital > 0 else 0

                if trades >= 5 and win_rate >= 75.0 and roi >= 60.0:
                    if pnl > best_long_pnl:
                        best_long_pnl = pnl
                        best_long_win_rate = win_rate
                        best_long_trades = trades
                        best_long_roi = roi
                        best_long_combo = f"{ent_name} & {ext_name}"
                        best_long_hold = hold
                        best_long_buy_price = buy_price
                        best_long_buy_date = buy_date
                        best_long_current_price = closes[-1] if len(closes) > 0 else 0
                        best_long_trades_list = temp_trades

        # ── 2. 空單最佳策略矩陣回測 ──
        best_short_combo = None
        best_short_pnl = -99999999
        best_short_win_rate = 0.0
        best_short_trades = 0
        best_short_roi = 0.0
        best_short_hold = False
        best_short_buy_price = 0.0
        best_short_buy_date = None
        best_short_current_price = 0.0
        best_short_trades_list = []

        for ent_name, ent_sig in short_entries:
            for ext_name, tp, sl, ext_sig in short_exits:
                shares = 1000
                pnl = 0
                trades = 0
                wins = 0
                hold = False
                short_price = 0
                short_date = None
                max_capital = 0
                temp_trades = []

                for i in range(1, n_rows - 1):
                    if not hold:
                        if ent_sig[i]:
                            hold = True
                            short_price = opens[i+1]
                            try:
                                short_date = str(int(float(df.iloc[i+1, 0])))
                            except Exception:
                                short_date = str(df.iloc[i+1, 0]).strip()
                            trades += 1
                            max_capital = max(max_capital, short_price * shares)
                    else:
                        next_open = opens[i+1]
                        trade_roi = (short_price - next_open) / short_price if short_price > 0 else 0
                        
                        cond_tp = (tp is not None) and (trade_roi >= tp)
                        cond_sl = (sl is not None) and (trade_roi <= -sl)
                        cond_signal = ext_sig[i]

                        if cond_tp or cond_sl or cond_signal:
                            hold = False
                            cover_price = next_open
                            trade_pnl = (short_price - cover_price) * shares
                            pnl += trade_pnl
                            if trade_pnl > 0:
                                wins += 1
                            
                            try:
                                exit_date = str(int(float(df.iloc[i+1, 0])))
                            except Exception:
                                exit_date = str(df.iloc[i+1, 0]).strip()

                            temp_trades.append({
                                "code": code,
                                "name": name,
                                "type": "short",
                                "strategy": f"{ent_name} & {ext_name}",
                                "posType": "空單",
                                "entryDate": short_date,
                                "entryPrice": short_price,
                                "exitDate": exit_date,
                                "exitPrice": cover_price,
                                "pnl": trade_pnl,
                                "roi": trade_roi * 100
                            })
                            short_price = 0
                            short_date = None

                win_rate = (wins / trades * 100) if trades > 0 else 0
                roi = (pnl / max_capital * 100) if max_capital > 0 else 0

                if trades >= 5 and win_rate >= 75.0 and roi >= 60.0:
                    if pnl > best_short_pnl:
                        best_short_pnl = pnl
                        best_short_win_rate = win_rate
                        best_short_trades = trades
                        best_short_roi = roi
                        best_short_combo = f"{ent_name} & {ext_name}"
                        best_short_hold = hold
                        best_short_buy_price = short_price
                        best_short_buy_date = short_date
                        best_short_current_price = closes[-1] if len(closes) > 0 else 0
                        best_short_trades_list = temp_trades

        # ── 3. 寫入排行榜數據結構 ──
        if best_long_combo is not None:
            holding_obj = None
            if best_long_hold:
                holding_pnl = (best_long_current_price - best_long_buy_price) * 1000
                holding_roi = ((best_long_current_price - best_long_buy_price) / best_long_buy_price * 100) if best_long_buy_price > 0 else 0
                holding_obj = {
                    "hold": True,
                    "buyDate": best_long_buy_date,
                    "buyPrice": best_long_buy_price,
                    "currentPrice": best_long_current_price,
                    "pnl": holding_pnl,
                    "roi": holding_roi,
                    "shares": 1.0,
                    "posType": "多單"
                }

            leaderboard_data.append({
                "code": code,
                "name": name,
                "type": "long",
                "strategy": best_long_combo,
                "profit": best_long_pnl,
                "roi": best_long_roi,
                "winRate": best_long_win_rate,
                "trades": best_long_trades,
                "holding": holding_obj
            })
            trade_cycles_log.extend(best_long_trades_list)
            success_count += 1
            print(f"  [LONG SUCCESS] {code} {name:4s} | WinRate: {best_long_win_rate:5.1f}% | Profit: {best_long_pnl:+10,.0f} | Trades: {best_long_trades:3d} | Strategy: {best_long_combo} | Holding: {best_long_hold}")

        if best_short_combo is not None:
            holding_obj = None
            if best_short_hold:
                holding_pnl = (best_short_buy_price - best_short_current_price) * 1000
                holding_roi = ((best_short_buy_price - best_short_current_price) / best_short_buy_price * 100) if best_short_buy_price > 0 else 0
                holding_obj = {
                    "hold": True,
                    "buyDate": best_short_buy_date,
                    "buyPrice": best_short_buy_price,
                    "currentPrice": best_short_current_price,
                    "pnl": holding_pnl,
                    "roi": holding_roi,
                    "shares": 1.0,
                    "posType": "空單"
                }

            leaderboard_data.append({
                "code": code,
                "name": name,
                "type": "short",
                "strategy": best_short_combo,
                "profit": best_short_pnl,
                "roi": best_short_roi,
                "winRate": best_short_win_rate,
                "trades": best_short_trades,
                "holding": holding_obj
            })
            trade_cycles_log.extend(best_short_trades_list)
            success_count += 1
            print(f"  [SHORT SUCCESS] {code} {name:4s} | WinRate: {best_short_win_rate:5.1f}% | Profit: {best_short_pnl:+10,.0f} | Trades: {best_short_trades:3d} | Strategy: {best_short_combo} | Holding: {best_short_hold}")

        if processed_count % 50 == 0:
            print(f"[Progress] Processed {processed_count}/{total_files} stocks...")

    # 4. 寫入排行榜與交易歷史
    if leaderboard_data:
        leaderboard_data.sort(key=lambda x: x["profit"], reverse=True)
        os.makedirs(os.path.dirname(OUTPUT_LEADERBOARD_PATH), exist_ok=True)
        
        with open(OUTPUT_LEADERBOARD_PATH, 'w', encoding='utf-8') as f:
            json.dump(leaderboard_data, f, indent=4, ensure_ascii=False, cls=NumpyEncoder)
        
        with open(OUTPUT_TRADES_PATH, 'w', encoding='utf-8') as f:
            json.dump(trade_cycles_log, f, indent=4, ensure_ascii=False, cls=NumpyEncoder)

        print(f"\n[Done] Search finished! Found {success_count} strategy targets with win rate >= 75%!")
        print(f"Leaderboard written to {OUTPUT_LEADERBOARD_PATH}")
        print(f"Trade history written to {OUTPUT_TRADES_PATH}")
    else:
        print("\n[Warning] No strategy target combination achieved criteria!")

if __name__ == "__main__":
    main()
