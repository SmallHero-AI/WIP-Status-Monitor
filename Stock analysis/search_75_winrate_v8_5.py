# -*- coding: utf-8 -*-
"""
================================================================================
  V8.5 雙向（多單/空單）75%勝率策略極速多核心回測引擎
================================================================================
"""

import os
import sys
import glob
import json
import pandas as pd
import numpy as np
import re
import warnings
from concurrent.futures import ProcessPoolExecutor, as_completed

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

warnings.filterwarnings('ignore')

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.int64, np.int32, np.int16, np.int8)):
            return int(obj)
        elif isinstance(obj, (np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

SCRIPT_DIR = r"E:\G-AI-1\Stock analysis"
STOCK_ORIGINAL_DIR = os.path.join(SCRIPT_DIR, "Stock original")
AUTO_EXPORT_DIR = os.path.join(STOCK_ORIGINAL_DIR, "auto_export")
OUTPUT_LEADERBOARD_PATH = os.path.join(SCRIPT_DIR, "修正版_V6_Server", "public", "leaderboard_v8_5.json")
OUTPUT_TRADES_PATH = os.path.join(SCRIPT_DIR, "修正版_V6_Server", "public", "trades_v8_5.json")

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

def process_single_stock(filepath):
    fname = os.path.basename(filepath)
    match = re.match(r'^(\d{4})_(.+?)_', fname)
    if match:
        code = match.group(1)
        name = match.group(2)
    else:
        code = fname.split('_')[0]
        name = code

    try:
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath, encoding='cp950')
        else:
            df = pd.read_excel(filepath)
    except Exception:
        try:
            df = pd.read_csv(filepath, encoding='utf-8')
        except Exception:
            return None

    if len(df) < 60:
        return None

    c_close = find_column(df, ['收盤價', 'Close', '收盤'])
    c_open  = find_column(df, ['開盤價', 'Open', '開盤'])
    c_high  = find_column(df, ['最高價', 'High', '最高'])
    c_low   = find_column(df, ['最低價', 'Low', '最低'])
    c_vol   = find_column(df, ['成交量', 'Volume', '張數'])
    c_ma5   = find_column(df, ['MA5', '5日均價', '均價[5]'])
    c_ma20  = find_column(df, ['MA20', '20日均價', '均價[20]'])
    c_ma60  = find_column(df, ['MA60', '60日均價', '均價[60]'])
    c_ma120 = find_column(df, ['MA120', '120日均價', '均價[120]'])
    c_k     = find_column(df, ['K[9,3,3]', 'KD_K', 'K值'])
    c_d     = find_column(df, ['D[9,3,3]', 'KD_D', 'D值'])
    c_rsi   = find_column(df, ['RSI', 'RSI[14]'])
    c_macd  = find_column(df, ['MACD 柱狀體', 'MACD_Hist', '柱狀體'])
    c_eom   = find_column(df, ['EOM[60]', 'EOM_60'])

    closes = clean_and_parse_series(df, c_close)
    opens  = clean_and_parse_series(df, c_open)
    highs  = clean_and_parse_series(df, c_high)
    lows   = clean_and_parse_series(df, c_low)
    vols   = clean_and_parse_series(df, c_vol)
    ma5    = clean_and_parse_series(df, c_ma5)
    ma20   = clean_and_parse_series(df, c_ma20)
    ma60   = clean_and_parse_series(df, c_ma60)
    ma120  = clean_and_parse_series(df, c_ma120)
    k_vals = clean_and_parse_series(df, c_k)
    d_vals = clean_and_parse_series(df, c_d)
    rsi    = clean_and_parse_series(df, c_rsi)
    macd   = clean_and_parse_series(df, c_macd)
    eom    = clean_and_parse_series(df, c_eom)

    n_rows = len(closes)
    if n_rows < 60:
        return None

    # ── 向量化技術條件 ──
    f_bull_ma = (closes > ma5) & (ma5 > ma20) & (ma20 > ma60)
    f_bear_ma = (closes < ma5) & (ma5 < ma20) & (ma20 < ma60)
    k_prev = np.roll(k_vals, 1); k_prev[0] = k_vals[0]
    d_prev = np.roll(d_vals, 1); d_prev[0] = d_vals[0]
    f_kd_gold = (k_prev <= d_prev) & (k_vals > d_vals)
    f_kd_dead = (k_prev >= d_prev) & (k_vals < d_vals)
    
    f_rsi_bull = (rsi > 50) & (rsi > np.roll(rsi, 1))
    f_rsi_low_turn = (rsi < 45) & (rsi > np.roll(rsi, 1))
    f_rsi_overbought = rsi > 70
    f_rsi_oversold = rsi < 30
    
    macd_prev = np.roll(macd, 1); macd_prev[0] = macd[0]
    f_macd_grow = (macd_prev <= 0) & (macd > 0)
    f_macd_shrink = (macd_prev >= 0) & (macd < 0)
    
    f_eom_bullish = eom > np.roll(eom, 1)
    f_eom_bearish = eom < np.roll(eom, 1)
    
    pp = (highs + lows + closes) / 3.0
    r1 = 2 * pp - lows
    s1 = 2 * pp - highs
    f_break_r1 = closes > r1
    f_break_s1 = closes < s1
    f_above_pivot = closes > pp
    f_below_pivot = closes < pp

    tp_mid = (highs + lows + closes) / 3.0
    mf_raw = tp_mid * vols
    mf_prev = np.roll(tp_mid, 1); mf_prev[0] = tp_mid[0]
    pos_mf = np.where(tp_mid > mf_prev, mf_raw, 0)
    neg_mf = np.where(tp_mid < mf_prev, mf_raw, 0)
    pos_mf_s = pd.Series(pos_mf).rolling(14, min_periods=1).sum().values
    neg_mf_s = pd.Series(neg_mf).rolling(14, min_periods=1).sum().values
    mfi = np.where(neg_mf_s == 0, 100, 100 - (100 / (1 + pos_mf_s / np.where(neg_mf_s == 0, 1e-9, neg_mf_s))))
    f_mfi_overbought = mfi > 80
    f_mfi_oversold = mfi < 20

    bias20 = np.where(ma20 == 0, 0, (closes - ma20) / ma20 * 100)
    f_bias_oversold = bias20 < -5.0
    f_bias_overbought = bias20 > 5.0

    tr = np.maximum(highs - lows, np.maximum(np.abs(highs - np.roll(closes, 1)), np.abs(lows - np.roll(closes, 1))))
    atr = pd.Series(tr).rolling(14, min_periods=1).mean().values

    std20 = pd.Series(closes).rolling(20, min_periods=1).std().values
    bb_upper = ma20 + 2 * std20
    bb_lower = ma20 - 2 * std20
    f_bb_oversold = closes <= bb_lower
    f_bb_overbought = closes >= bb_upper

    # 定義策略組合
    long_entries = [
        ("強勢均線多頭+KD金叉", f_bull_ma & f_kd_gold),
        ("中長期多頭+RSI低檔轉強", (closes > ma60) & f_rsi_low_turn),
        ("雙重均線突破+MACD翻紅", (closes > ma20) & (ma20 > ma60) & f_macd_grow),
        ("EOM動能突破+均線多頭", f_eom_bullish & f_bull_ma),
        ("突破阻力(R1)+MACD多頭", f_break_r1 & (macd > 0)),
        ("突破樞軸(Pivot)+RSI轉強", f_above_pivot & f_rsi_bull),
        ("多頭拉回：MA60之上+KD金叉+RSI<45", (closes > ma60) & f_kd_gold & (rsi < 45)),
        ("動能共振：EOM突破+MACD>0+RSI>50", f_eom_bullish & (macd > 0) & (rsi > 50)),
        ("壓力突破：價格>R1+EOM強勢+MACD>0", f_break_r1 & f_eom_bullish & (macd > 0)),
        ("長期均線支撐：站上MA120+KD金叉+CCI超賣", (closes > ma120) & f_kd_gold & f_bias_oversold),
        ("雙重超賣 (RSI+CCI)+MACD轉強", f_rsi_oversold & f_macd_grow),
        ("CCI超賣+MFI超賣+KD金叉", f_mfi_oversold & f_kd_gold),
        ("雙保險超跌：BIAS超賣+布林下軌觸及", f_bias_oversold & f_bb_oversold),
        ("極度超跌共振 (BIAS+RSI+MFI)", f_bias_oversold & f_rsi_oversold & f_mfi_oversold),
        ("樞軸點(S1)支撐+KD金叉", (closes > s1) & f_kd_gold),
        ("S1支撐不破+MACD紅柱增長", (closes > s1) & f_macd_grow),
        ("布林中軌支撐+MACD紅柱", (closes > ma20) & (macd > 0))
    ]

    long_exits = [
        ("6%停利 / 6%停損 (穩健型)", 0.06, 0.06, f_kd_dead),
        ("8%停利 / 8%停損 (精配型)", 0.08, 0.08, f_kd_dead),
        ("10%停利 / 6%停損 (波段型)", 0.10, 0.06, f_kd_dead),
        ("12%停利 / 6%停損 (積極型)", 0.12, 0.06, f_kd_dead),
        ("RSI過熱(RSI>70)離場", 0.08, 0.06, f_rsi_overbought),
        ("MACD柱狀體縮小離場", 0.08, 0.06, f_macd_shrink),
        ("波段追蹤：ATR追蹤停損 (最高價拉回3*ATR離場)", None, 0.10, None)
    ]

    short_entries = [
        ("弱勢均線空頭+KD死叉", f_bear_ma & f_kd_dead),
        ("中長期空頭+RSI高檔轉弱", (closes < ma60) & f_rsi_overbought),
        ("雙重均線跌破+MACD翻綠", (closes < ma20) & (ma20 < ma60) & f_macd_shrink),
        ("EOM動能下跌+均線空頭", f_eom_bearish & f_bear_ma),
        ("跌破支撐(S1)+MACD空頭", f_break_s1 & (macd < 0)),
        ("跌破樞軸(Pivot)+RSI轉弱", f_below_pivot & (rsi < 50)),
        ("空頭拉回：MA60之外+KD死叉+RSI>55", (closes < ma60) & f_kd_dead & (rsi > 55)),
        ("動能共振：EOM下跌+MACD<0+RSI<50", f_eom_bearish & (macd < 0) & (rsi < 50)),
        ("支撐跌破：價格<S1+EOM弱勢+MACD<0", f_break_s1 & f_eom_bearish & (macd < 0)),
        ("長期均線阻力：跌破MA120+KD死叉+CCI超買", (closes < ma120) & f_kd_dead & f_bias_overbought),
        ("雙重超買 (RSI+CCI)+MACD轉弱", f_rsi_overbought & f_macd_shrink),
        ("CCI超買+MFI超買+KD死叉", f_mfi_overbought & f_kd_dead),
        ("雙保險超買：BIAS超買+布林上軌觸及", f_bias_overbought & f_bb_overbought),
        ("極度超買共振 (BIAS+RSI+MFI)", f_bias_overbought & f_rsi_overbought & f_mfi_overbought),
        ("樞軸點(R1)壓力+KD死叉", (closes < r1) & f_kd_dead),
        ("R1壓力不破+MACD綠柱增長", (closes < r1) & f_macd_shrink),
        ("布林中軌阻力+MACD綠柱", (closes < ma20) & (macd < 0))
    ]

    short_exits = [
        ("6%停利 / 6%停損 (穩健型)", 0.06, 0.06, f_kd_gold),
        ("8%停利 / 8%停損 (精配型)", 0.08, 0.08, f_kd_gold),
        ("10%停利 / 6%停損 (波段型)", 0.10, 0.06, f_kd_gold),
        ("12%停利 / 6%停損 (積極型)", 0.12, 0.06, f_kd_gold),
        ("RSI超賣(RSI<30)回補", 0.08, 0.06, f_rsi_oversold),
        ("MACD柱狀體增長回補", 0.08, 0.06, f_macd_grow)
    ]

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
    best_long_signal_info = None

    for ent_name, ent_sig in long_entries:
        if np.sum(ent_sig) < 5:
            continue
        for ext_name, tp, sl, ext_sig in long_exits:
            shares = 1000
            pnl = 0
            trades = 0
            wins = 0
            hold = False
            buy_price = 0
            buy_date = None
            highest_since_entry = 0
            max_capital = 0
            temp_trades = []
            last_signal_info = None

            for i in range(n_rows - 1):
                curr_close = closes[i]
                next_open = opens[i + 1]
                try:
                    date_str = str(int(float(df.iloc[i + 1, 0])))
                except Exception:
                    date_str = str(df.iloc[i + 1, 0]).strip()

                if not hold:
                    if ent_sig[i]:
                        hold = True
                        buy_price = next_open
                        buy_date = date_str
                        highest_since_entry = buy_price
                        trades += 1
                        if buy_price * shares > max_capital:
                            max_capital = buy_price * shares
                else:
                    highest_since_entry = max(highest_since_entry, highs[i])
                    trade_roi = (curr_close - buy_price) / buy_price
                    cond_tp = (tp is not None) and (trade_roi >= tp)
                    cond_sl = (sl is not None) and (trade_roi <= -sl)
                    cond_signal = ext_sig[i] if ext_sig is not None else False
                    if ext_name == "波段追蹤：ATR追蹤停損 (最高價拉回3*ATR離場)":
                        cond_signal = curr_close < (highest_since_entry - 3 * atr[i])
                        cond_sl = trade_roi <= -0.10

                    if cond_tp or cond_sl or cond_signal:
                        hold = False
                        sell_price = next_open
                        trade_pnl = (sell_price - buy_price) * shares
                        pnl += trade_pnl
                        if trade_pnl > 0:
                            wins += 1
                        temp_trades.append({
                            "code": code,
                            "name": name,
                            "type": "long",
                            "strategy": f"{ent_name} & {ext_name}",
                            "posType": "多單",
                            "entryDate": buy_date,
                            "entryPrice": buy_price,
                            "exitDate": date_str,
                            "exitPrice": sell_price,
                            "pnl": trade_pnl,
                            "roi": trade_roi * 100
                        })
                        buy_price = 0
                        buy_date = None

            # 最新一日三態訊號精準判定
            latest_close = closes[-1]
            latest_date_str = str(df.iloc[-1, 0]).strip()
            if hold:
                highest_since_entry = max(highest_since_entry, highs[-1])
                trade_roi = (latest_close - buy_price) / buy_price
                cond_tp = (tp is not None) and (trade_roi >= tp)
                cond_sl = (sl is not None) and (trade_roi <= -sl)
                cond_signal = ext_sig[-1] if ext_sig is not None else False
                if ext_name == "波段追蹤：ATR追蹤停損 (最高價拉回3*ATR離場)":
                    cond_signal = latest_close < (highest_since_entry - 3 * atr[-1])
                    cond_sl = trade_roi <= -0.10

                if cond_tp or cond_sl or cond_signal:
                    reason_type = "TAKE_PROFIT" if cond_tp else ("STOP_LOSS" if cond_sl else "SIGNAL_EXIT")
                    reason_text = "🎯 停利平倉" if cond_tp else ("🛑 觸發停損" if cond_sl else "📊 策略指標轉弱離場")
                    last_signal_info = {
                        "status": "TRIGGER_EXIT",
                        "direction": "多單",
                        "triggerDate": latest_date_str,
                        "targetExitDate": "明日開盤",
                        "entryPrice": round(buy_price, 2),
                        "currentPrice": round(latest_close, 2),
                        "pnl": round((latest_close - buy_price) * shares, 2),
                        "roi": round(trade_roi * 100, 2),
                        "tpPrice": round(buy_price * (1 + tp), 2) if tp else None,
                        "slPrice": round(buy_price * (1 - sl), 2) if sl else None,
                        "exitReasonType": reason_type,
                        "exitReasonText": reason_text,
                        "reason": f"今日觸發多頭出場條件 [{ext_name} - {reason_text}] (預計明日開盤平倉)"
                    }
                else:
                    last_signal_info = {
                        "status": "HOLDING",
                        "direction": "多單",
                        "buyDate": buy_date,
                        "buyPrice": round(buy_price, 2),
                        "currentPrice": round(latest_close, 2),
                        "pnl": round((latest_close - buy_price) * shares, 2),
                        "roi": round(trade_roi * 100, 2),
                        "tpPrice": round(buy_price * (1 + tp), 2) if tp else None,
                        "slPrice": round(buy_price * (1 - sl), 2) if sl else None,
                        "reason": "持續持倉中"
                    }
            else:
                if ent_sig[-1]:
                    last_signal_info = {
                        "status": "TRIGGER_ENTRY",
                        "direction": "多單",
                        "triggerDate": latest_date_str,
                        "targetEntryDate": "明日開盤",
                        "targetEntryPrice": round(latest_close, 2),
                        "currentPrice": round(latest_close, 2),
                        "tpPrice": round(latest_close * (1 + tp), 2) if tp else None,
                        "slPrice": round(latest_close * (1 - sl), 2) if sl else None,
                        "reason": f"今日觸發多頭進場條件 [{ent_name}] (預計明日開盤買進)"
                    }

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
                    best_long_signal_info = last_signal_info

    # ── 空單最佳策略回測 ──
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
    best_short_signal_info = None

    for ent_name, ent_sig in short_entries:
        if np.sum(ent_sig) < 5:
            continue
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
            last_signal_info = None

            for i in range(n_rows - 1):
                curr_close = closes[i]
                next_open = opens[i + 1]
                try:
                    date_str = str(int(float(df.iloc[i + 1, 0])))
                except Exception:
                    date_str = str(df.iloc[i + 1, 0]).strip()

                if not hold:
                    if ent_sig[i]:
                        hold = True
                        short_price = next_open
                        short_date = date_str
                        trades += 1
                        if short_price * shares > max_capital:
                            max_capital = short_price * shares
                else:
                    trade_roi = (short_price - curr_close) / short_price
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
                        temp_trades.append({
                            "code": code,
                            "name": name,
                            "type": "short",
                            "strategy": f"{ent_name} & {ext_name}",
                            "posType": "空單",
                            "entryDate": short_date,
                            "entryPrice": short_price,
                            "exitDate": date_str,
                            "exitPrice": cover_price,
                            "pnl": trade_pnl,
                            "roi": trade_roi * 100
                        })
                        short_price = 0
                        short_date = None

            latest_close = closes[-1]
            latest_date_str = str(df.iloc[-1, 0]).strip()
            if hold:
                trade_roi = (short_price - latest_close) / short_price
                cond_tp = (tp is not None) and (trade_roi >= tp)
                cond_sl = (sl is not None) and (trade_roi <= -sl)
                cond_signal = ext_sig[-1]

                if cond_tp or cond_sl or cond_signal:
                    reason_type = "TAKE_PROFIT" if cond_tp else ("STOP_LOSS" if cond_sl else "SIGNAL_EXIT")
                    reason_text = "🎯 停利回補" if cond_tp else ("🛑 觸發停損" if cond_sl else "📊 策略指標回補離場")
                    last_signal_info = {
                        "status": "TRIGGER_EXIT",
                        "direction": "空單",
                        "triggerDate": latest_date_str,
                        "targetExitDate": "明日開盤",
                        "entryPrice": round(short_price, 2),
                        "currentPrice": round(latest_close, 2),
                        "pnl": round((short_price - latest_close) * shares, 2),
                        "roi": round(trade_roi * 100, 2),
                        "tpPrice": round(short_price * (1 - tp), 2) if tp else None,
                        "slPrice": round(short_price * (1 + sl), 2) if sl else None,
                        "exitReasonType": reason_type,
                        "exitReasonText": reason_text,
                        "reason": f"今日觸發空頭出場條件 [{ext_name} - {reason_text}] (預計明日開盤回補)"
                    }
                else:
                    last_signal_info = {
                        "status": "HOLDING",
                        "direction": "空單",
                        "buyDate": short_date,
                        "buyPrice": round(short_price, 2),
                        "currentPrice": round(latest_close, 2),
                        "pnl": round((short_price - latest_close) * shares, 2),
                        "roi": round(trade_roi * 100, 2),
                        "tpPrice": round(short_price * (1 - tp), 2) if tp else None,
                        "slPrice": round(short_price * (1 + sl), 2) if sl else None,
                        "reason": "持續空單持倉中"
                    }
            else:
                if ent_sig[-1]:
                    last_signal_info = {
                        "status": "TRIGGER_ENTRY",
                        "direction": "空單",
                        "triggerDate": latest_date_str,
                        "targetEntryDate": "明日開盤",
                        "targetEntryPrice": round(latest_close, 2),
                        "currentPrice": round(latest_close, 2),
                        "tpPrice": round(latest_close * (1 - tp), 2) if tp else None,
                        "slPrice": round(latest_close * (1 + sl), 2) if sl else None,
                        "reason": f"今日觸發空頭進場條件 [{ent_name}] (預計明日開盤賣空)"
                    }

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
                    best_short_signal_info = last_signal_info

    long_res = None
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
                "posType": "多單",
                "tpPrice": best_long_signal_info.get("tpPrice") if best_long_signal_info else None,
                "slPrice": best_long_signal_info.get("slPrice") if best_long_signal_info else None
            }

        long_res = {
            "code": code,
            "name": name,
            "type": "long",
            "strategy": best_long_combo,
            "profit": best_long_pnl,
            "roi": best_long_roi,
            "winRate": best_long_win_rate,
            "trades": best_long_trades,
            "holding": holding_obj,
            "signalInfo": best_long_signal_info
        }

    short_res = None
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
                "posType": "空單",
                "tpPrice": best_short_signal_info.get("tpPrice") if best_short_signal_info else None,
                "slPrice": best_short_signal_info.get("slPrice") if best_short_signal_info else None
            }

        short_res = {
            "code": code,
            "name": name,
            "type": "short",
            "strategy": best_short_combo,
            "profit": best_short_pnl,
            "roi": best_short_roi,
            "winRate": best_short_win_rate,
            "trades": best_short_trades,
            "holding": holding_obj,
            "signalInfo": best_short_signal_info
        }

    all_trades = best_long_trades_list + best_short_trades_list
    return (long_res, short_res, all_trades)

def main():
    print("=" * 60)
    print("  [Start] 75% Win Rate Matrix Search Engine V8.5 (多核心極速版)...")
    print("=" * 60)

    candidate_files = []
    for folder in [AUTO_EXPORT_DIR, STOCK_ORIGINAL_DIR]:
        if os.path.exists(folder):
            candidate_files.extend(glob.glob(os.path.join(folder, "*.xlsx")))
            candidate_files.extend(glob.glob(os.path.join(folder, "*.csv")))

    code_file_map = {}
    for fpath in candidate_files:
        fname = os.path.basename(fpath)
        m = re.match(r'^(\d{4})_', fname)
        if m:
            code = m.group(1)
            def get_fdate(path):
                match = re.search(r'\d{8}', os.path.basename(path))
                return match.group(0) if match else "00000000"
            
            fdate = get_fdate(fpath)
            is_xlsx = fpath.endswith('.xlsx')
            if code not in code_file_map:
                code_file_map[code] = (fdate, is_xlsx, fpath)
            else:
                curr_date, curr_xlsx, _ = code_file_map[code]
                if (fdate > curr_date) or (fdate == curr_date and is_xlsx and not curr_xlsx):
                    code_file_map[code] = (fdate, is_xlsx, fpath)

    stock_files = [v[2] for v in code_file_map.values()]
    print(f"[Info] Found {len(stock_files)} unique stock data files for V8.5 backtest.")

    leaderboard_data = []
    trade_cycles_log = []
    success_count = 0

    workers = max(1, os.cpu_count() - 1)
    print(f"🚀 [多線程加速] 開啟 {workers} 個 CPU 核心進行平行矩陣運算...")

    with ProcessPoolExecutor(max_workers=workers) as executor:
        future_to_file = {executor.submit(process_single_stock, f): f for f in stock_files}
        completed = 0
        total = len(stock_files)
        for future in as_completed(future_to_file):
            completed += 1
            res = future.result()
            if res:
                long_res, short_res, trades = res
                if long_res:
                    leaderboard_data.append(long_res)
                    success_count += 1
                if short_res:
                    leaderboard_data.append(short_res)
                    success_count += 1
                if trades:
                    trade_cycles_log.extend(trades)

            if completed % 100 == 0 or completed == total:
                print(f"[Progress] 已完成 {completed}/{total} 檔個股 ({completed/total*100:.1f}%), 已篩選出 {success_count} 策略標的...", flush=True)

    if leaderboard_data:
        leaderboard_data.sort(key=lambda x: x["profit"], reverse=True)
        os.makedirs(os.path.dirname(OUTPUT_LEADERBOARD_PATH), exist_ok=True)
        
        with open(OUTPUT_LEADERBOARD_PATH, 'w', encoding='utf-8') as f:
            json.dump(leaderboard_data, f, indent=4, ensure_ascii=False, cls=NumpyEncoder)
        
        with open(OUTPUT_TRADES_PATH, 'w', encoding='utf-8') as f:
            json.dump(trade_cycles_log, f, indent=4, ensure_ascii=False, cls=NumpyEncoder)

        print(f"\n🎉 [Done] 全數 {total} 檔個股極速回測完成！共篩選出 {success_count} 個高勝率策略標的。")
        print(f"Leaderboard 寫入: {OUTPUT_LEADERBOARD_PATH}")
        print(f"Trade History 寫入: {OUTPUT_TRADES_PATH}")
    else:
        print("\n[Warning] 無符合條件之策略標的！")

if __name__ == "__main__":
    main()
