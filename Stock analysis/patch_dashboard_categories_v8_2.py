# -*- coding: utf-8 -*-
import json
import os

SCRIPT_DIR = r"E:\G-AI-1\Stock analysis"
HTML_BASE_PATH = os.path.join(SCRIPT_DIR, "修正版_V6_Server", "public", "dashboard_v8_2_backup.html")
HTML_OUT_PATH = os.path.join(SCRIPT_DIR, "修正版_V6_Server", "public", "dashboard_v8_2.html")
SERVER_PATH = os.path.join(SCRIPT_DIR, "修正版_V6_Server", "server.js")
LEADERBOARD_PATH = os.path.join(SCRIPT_DIR, "修正版_V6_Server", "public", "leaderboard_v8_2.json")

def main():
    print("=" * 60)
    print("  AI 策略分類網頁編譯工具 V8.2 (多尺度自適應型態策略版)...")
    print("=" * 60)

    if not os.path.exists(LEADERBOARD_PATH):
        print(f"[錯誤] {LEADERBOARD_PATH} 不存在！")
        return

    with open(LEADERBOARD_PATH, 'r', encoding='utf-8') as f:
        leaderboard = json.load(f)

    # 篩選勝率 >= 75% 且 ROI >= 60% 的股票
    high_win = [x for x in leaderboard if x['winRate'] >= 75 and x.get('roi', 0) >= 60]
    print(f"[資訊] 共讀到 {len(high_win)} 檔高勝率且高 ROI 個股")

    # 分類策略定義 (多單進場訊號)
    long_trend = [
        "強勢均線多頭+KD金叉", "中長期多頭+RSI低檔轉強", "雙重均線突破+MACD翻紅", 
        "EOM動能突破+均線多頭", "突破阻力(R1)+MACD多頭", "突破樞軸(Pivot)+RSI轉強", 
        "多頭拉回：MA60之上+KD金叉+RSI<45", "動能共振：EOM突破+MACD>0+RSI>50", 
        "壓力突破：價格>R1+EOM強勢+MACD>0", "長期均線支撐：站上MA120+KD金叉+CCI超賣",
        "W底雙重底突破頸線 (多頭趨勢)", "頭肩底突破頸線確立 (多頭趨勢)",
        "三角收斂突破上軌加速 (多頭整理)", "箱型整理突破阻力上限 (多頭整理)"
    ]
    long_rebound = ["雙重超賣 (RSI+CCI)+MACD轉強", "CCI超賣+MFI超賣+KD金叉", "V型反轉爆量向上拉升 (多頭趨勢)"]
    long_oversold = ["雙保險超跌：BIAS超賣+布林下軌觸及", "極度超跌共振 (BIAS+RSI+MFI)"]
    long_support = ["樞軸點(S1)支撐+KD金叉", "S1支撐不破+MACD紅柱增長", "布林中軌支撐+MACD紅柱", "CCI超賣反彈+MACD紅柱增長"]

    # 分類策略定義 (空單進場訊號)
    short_trend = [
        "弱勢均線空頭+KD死叉", "中長期空頭+RSI高檔轉弱", "雙重均線跌破+MACD翻綠",
        "EOM動能下跌+均線空頭", "跌破支撐(S1)+MACD空頭", "跌破樞軸(Pivot)+RSI轉弱",
        "空頭拉回：MA60之外+KD死叉+RSI>55", "動能共振：EOM下跌+MACD<0+RSI<50",
        "支撐跌破：價格<S1+EOM弱勢+MACD<0", "長期均線阻力：跌破MA120+KD死叉+CCI超買",
        "M頭雙重頂跌破頸線 (空頭趨勢)", "頭肩頂跌破頸線反轉 (空頭趨勢)",
        "三角收斂跌破下軌加速 (空頭整理)", "箱型整理跌破支撐下限 (空頭整理)"
    ]
    short_rebound = ["雙重超買 (RSI+CCI)+MACD轉弱", "CCI超買+MFI超買+KD死叉", "倒V型反轉急速暴跌 (空頭趨勢)"]
    short_oversold = ["雙保險超買：BIAS超買+布林上軌觸及", "極度超買共振 (BIAS+RSI+MFI)"]
    short_support = ["樞軸點(R1)壓力+KD死叉", "R1壓力不破+MACD綠柱增長", "布林中軌阻力+MACD綠柱", "CCI超買回檔+MACD綠柱增長"]

    new_stocks = []
    new_xlsx = {}

    for item in high_win:
        code = item['code']
        name = item['name']
        strategy_type = item.get('type', 'long')
        strategy_full = item['strategy']
        parts = strategy_full.split(' & ')
        entry = parts[0].strip()
        exit_cond = parts[1].strip()

        # 分類判斷
        strat_cat = 'ai_trend'
        if strategy_type == 'long':
            if entry in long_trend: strat_cat = 'ai_trend'
            elif entry in long_rebound: strat_cat = 'ai_rebound'
            elif entry in long_oversold: strat_cat = 'ai_oversold'
            elif entry in long_support: strat_cat = 'ai_support'
        else:
            if entry in short_trend: strat_cat = 'ai_trend'
            elif entry in short_rebound: strat_cat = 'ai_rebound'
            elif entry in short_oversold: strat_cat = 'ai_oversold'
            elif entry in short_support: strat_cat = 'ai_support'

        tp = 0.0
        sl = 0.0
        if "6%停利 / 6%停損" in exit_cond:
            tp, sl = 6.0, 6.0
        elif "8%停利 / 8%停損" in exit_cond:
            tp, sl = 8.0, 8.0
        elif "12%停利 / 6%停損" in exit_cond:
            tp, sl = 12.0, 6.0
        elif "KD" in exit_cond or "死叉" in exit_cond or "金叉" in exit_cond:
            sl = 6.0
        elif "RSI" in exit_cond:
            sl = 6.0
        elif "MACD" in exit_cond:
            sl = 6.0
        elif "MA20" in exit_cond:
            sl = 6.0
        elif "布林" in exit_cond:
            sl = 6.0
        elif "支撐" in exit_cond or "壓力" in exit_cond:
            tp = 8.0

        new_stocks.append({
            'id': f's{code}_ai',
            'name': name,
            'strategy': strat_cat,
            'filename': f'{code}_AI_v8_2.xlsx',
            'entry': entry,
            'exit': exit_cond,
            'tp': tp,
            'sl': sl,
            'type': strategy_type
        })
        new_xlsx[f's{code}_ai'] = f'{code}_AI_v8_2.xlsx'

    # 原本的 12 支預設個股 (均為 long)
    base_stocks = [
        { 'id': 's2330', 'name': '台積電', 'strategy': 'v4', 'filename': '2330_台積電_V4_高勝率回測.xlsx', 'type': 'long' },
        { 'id': 's2360', 'name': '致茂', 'strategy': 'v4', 'filename': '2360_致茂_V4_高勝率回測.xlsx', 'type': 'long' },
        { 'id': 's6205', 'name': '詮欣', 'strategy': 'v4', 'filename': '6205_詮欣_V4_高勝率回測.xlsx', 'type': 'long' },
        { 'id': 's6274', 'name': '台耀', 'strategy': 'v4', 'filename': '6274_台耀_V4_高勝率回測.xlsx', 'type': 'long' },
        { 'id': 's6669', 'name': '緯穎', 'strategy': 'rebound', 'filename': '6669_緯穎_V_Rebound_高勝率回測.xlsx', 'type': 'long' },
        { 'id': 's3189', 'name': '景碩', 'strategy': 'rebound', 'filename': '3189_景碩_V_Rebound_高勝率回測.xlsx', 'type': 'long' },
        { 'id': 's3455', 'name': '由田', 'strategy': 'rebound', 'filename': '3455_由田_V_Rebound_高勝率回測.xlsx', 'type': 'long' },
        { 'id': 's3535', 'name': '晶彩科', 'strategy': 'rebound', 'filename': '3535_晶彩科_V_Rebound_高勝率回測.xlsx', 'type': 'long' },
        { 'id': 's4908', 'name': '前鼎', 'strategy': 'rebound', 'filename': '4908_前鼎_V_Rebound_高勝率回測.xlsx', 'type': 'long' },
        { 'id': 's6269', 'name': '台郡', 'strategy': 'rebound', 'filename': '6269_台郡_V_Rebound_高勝率回測.xlsx', 'type': 'long' },
        { 'id': 's3443', 'name': '創意', 'strategy': 'v38', 'filename': '3443_創意_V_Rebound_高勝率回測.xlsx', 'type': 'long' },
        { 'id': 's6261', 'name': '久元', 'strategy': 'dipbuy', 'filename': '6261_久元_V_Dip_Buy_高勝率回測.xlsx', 'type': 'long' }
    ]
    all_stocks = base_stocks + new_stocks

    base_xlsx = {
        's2330': '2330_台積電_V4_高勝率回測.xlsx',
        's2360': '2360_致茂_V4_高勝率回測.xlsx',
        's6205': '6205_詮欣_V4_高勝率回測.xlsx',
        's6669': '6669_緯穎_V_Rebound_高勝率回測.xlsx',
        's3443': '3443_創意_V_Rebound_高勝率回測.xlsx',
        's3189': '3189_景碩_V_Rebound_高勝率回測.xlsx',
        's3455': '3455_由田_V_Rebound_高勝率回測.xlsx',
        's3535': '3535_晶彩科_V_Rebound_高勝率回測.xlsx',
        's4908': '4908_前鼎_V_Rebound_高勝率回測.xlsx',
        's6269': '6269_台郡_V_Rebound_高勝率回測.xlsx',
        's6274': '6274_台耀_V4_高勝率回測.xlsx',
        's6261': '6261_久元_V_Dip_Buy_高勝率回測.xlsx'
    }
    base_xlsx.update(new_xlsx)

    # 讀取備份 HTML 檔案作為基礎
    with open(HTML_BASE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    # ── 1. 注入新 preloadedStocks 與 xlsxFiles ──
    stocks_js = json.dumps(all_stocks, indent=8, ensure_ascii=False)
    xlsx_js = json.dumps(base_xlsx, indent=8, ensure_ascii=False)

    start_stocks_idx = content.find("const preloadedStocks = [")
    end_stocks_idx = content.find("];", start_stocks_idx)
    if start_stocks_idx != -1 and end_stocks_idx != -1:
        old_stocks_block = content[start_stocks_idx:end_stocks_idx+2]
        new_stocks_block = f"const preloadedStocks = {stocks_js};"
        content = content.replace(old_stocks_block, new_stocks_block)
        print("  [成功] 替換 preloadedStocks")

    start_xlsx_idx = content.find("const xlsxFiles = {")
    end_xlsx_idx = content.find("};", start_xlsx_idx)
    if start_xlsx_idx != -1 and end_xlsx_idx != -1:
        old_xlsx_block = content[start_xlsx_idx:end_xlsx_idx+2]
        new_xlsx_block = f"const xlsxFiles = {xlsx_js};"
        content = content.replace(old_xlsx_block, new_xlsx_block)
        print("  [成功] 替換 xlsxFiles")

    # 儲存修改後的 HTML 檔案
    with open(HTML_OUT_PATH, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  [成功] 儲存至 {HTML_OUT_PATH}")
    print("=" * 60)

if __name__ == "__main__":
    main()
