import pandas as pd
import numpy as np
import itertools
import os
import re

input_dir = "E:\\G-AI-1\\Stock analysis\\Stock original"
output_html = "E:\\G-AI-1\\Stock analysis\\技術分析測試_全個股_深度分析版.html"

# 定義 12 檔股票的獨立策略資訊
strategies = {
    '2330': {'name': '台積電', 'type': 'V4'},
    '3443': {'name': '創意', 'type': 'V38'},
    '2360': {'name': '致茂', 'type': 'MA_MFI_Rebound'},
    '6669': {'name': '緯穎', 'type': 'Dual_MA_MACD'},
    '3455': {'name': '由田', 'type': 'EOM_Break_Lock'},
    '3535': {'name': '晶彩科', 'type': 'MFI_Extreme'},
    '4746': {'name': '台耀', 'type': 'Vol_Breakout'},
    '4908': {'name': '前鼎', 'type': 'MACD_Pullback'},
    '3189': {'name': '景碩', 'type': 'MFI_MACD_Div'},
    '6205': {'name': '詮欣', 'type': 'MA60_MFI'},
    '6261': {'name': '久元', 'type': 'Triple_Confirm'},
    '6269': {'name': '台郡', 'type': 'Range_Fade'}
}

# 讀取資料快取
stock_data = {}
for file in os.listdir(input_dir):
    if file.endswith(".xlsx"):
        code = file.split('_')[0]
        if code in strategies:
            df = pd.read_excel(os.path.join(input_dir, file))
            df.columns = [str(c) for c in df.columns]
            for col in df.columns[1:]:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            stock_data[code] = df

# 針對每個股票執行精細網格搜尋 (小數點一位)
best_params_db = {}

def evaluate_strategy(df, params, strat_type):
    close_arr = df.iloc[:, 4].values
    open_arr = df.iloc[:, 1].values
    high_arr = df.iloc[:, 2].values
    ma20_arr = df.iloc[:, 7].values
    ma60_arr = df.iloc[:, 8].values
    eom_arr = df.iloc[:, 10].values
    eomsig_arr = df.iloc[:, 11].values
    mfi_arr = df.iloc[:, 12].values
    macd_arr = df.iloc[:, 14].values
    
    hold = False
    buy_price = 0.0
    pnls = []
    mPrf = 0
    
    for i in range(2, len(df)-1):
        c_close, n_open = close_arr[i], open_arr[i+1]
        c_ma20, c_ma60 = ma20_arr[i], ma60_arr[i]
        c_eom, c_eomsig = eom_arr[i], eomsig_arr[i]
        c_mfi, c_macd = mfi_arr[i], macd_arr[i]
        p_eom, p_eomsig = eom_arr[i-1], eomsig_arr[i-1]
        p_high, p_macd = high_arr[i-1], macd_arr[i-1]
        
        if not hold:
            entry = False
            if strat_type == 'V4':
                entry = c_close > c_ma20 and c_eom > (c_eomsig + params['eom_off']) and c_macd > params['macd'] and c_mfi > params['mfi']
            elif strat_type == 'V38':
                entry = (c_eom > (c_eomsig + params['eom_sens']) and p_eom <= (p_eomsig + params['eom_sens'])) and c_close > c_ma20 and c_close > p_high and c_macd > p_macd
            elif strat_type == 'MA_MFI_Rebound':
                entry = c_close > c_ma60 and c_mfi > params['mfi'] and c_eom > c_eomsig
            elif strat_type == 'Dual_MA_MACD':
                entry = c_close > c_ma20 and c_ma20 > c_ma60 and c_macd > params['macd']
            elif strat_type == 'EOM_Break_Lock':
                entry = c_eom > c_eomsig and p_eom <= p_eomsig and c_macd > 0
            elif strat_type == 'MFI_Extreme':
                entry = c_mfi < params['mfi_s'] and c_close > c_ma20
            elif strat_type == 'Vol_Breakout':
                entry = c_close > p_high and c_eom > (c_eomsig + params['eom_sens']) and c_mfi > 50
            elif strat_type == 'MACD_Pullback':
                entry = c_macd > 0 and c_macd < p_macd and c_close > c_ma20
            elif strat_type == 'MFI_MACD_Div':
                entry = c_mfi < params['mfi'] and c_macd > p_macd
            elif strat_type == 'MA60_MFI':
                entry = c_close > c_ma60 and c_mfi < params['mfi']
            elif strat_type == 'Triple_Confirm':
                entry = c_close > c_ma20 and c_eom > params['eom_th'] and c_macd > 0
            elif strat_type == 'Range_Fade':
                entry = c_close < c_ma20 and c_mfi < params['mfi']

            if entry:
                hold = True
                buy_price = n_open
                mPrf = 0
        else:
            pnlR = (n_open - buy_price) / buy_price
            curR = (c_close - buy_price) / buy_price
            mPrf = max(mPrf, curR)
            exit_flag = False
            
            if strat_type in ['V38', 'EOM_Break_Lock']:
                if mPrf >= params['tri'] and pnlR <= params['lock']: exit_flag = True
                elif c_eom < c_eomsig: exit_flag = True
                elif pnlR <= -params['sl']: exit_flag = True
            elif strat_type == 'Range_Fade':
                if c_close > c_ma20 or pnlR >= params['tp'] or pnlR <= -params['sl']: exit_flag = True
            else:
                if pnlR >= params['tp'] or pnlR <= -params['sl']: exit_flag = True
                
            if exit_flag:
                hold = False
                pnls.append((n_open - buy_price) * 1000)
    
    return sum(pnls)

print("開始深度精細分析...")
for code, info in strategies.items():
    if code not in stock_data: continue
    df = stock_data[code]
    strat = info['type']
    print(f"優化 {code} ({strat})...")
    
    best_pnl = -999999
    best_p = {}
    
    tp_grid = np.arange(0.05, 0.20, 0.01) # 5.0% to 19.0% step 1.0% (Using 0.01 internally = 1%)
    sl_grid = np.arange(0.03, 0.09, 0.01)
    
    if strat == 'V4':
        grids = itertools.product(tp_grid, sl_grid, [-0.5, 0.0, 0.5], [35, 40, 45])
        for tp, sl, macd, mfi in grids:
            p = {'tp':tp, 'sl':sl, 'macd':macd, 'mfi':mfi, 'eom_off':0}
            pnl = evaluate_strategy(df, p, strat)
            if pnl > best_pnl: best_pnl = pnl; best_p = p
    elif strat in ['V38', 'EOM_Break_Lock']:
        grids = itertools.product(np.arange(0.02, 0.08, 0.005), np.arange(0.01, 0.05, 0.005), sl_grid)
        for tri, lk, sl in grids:
            if tri <= lk: continue
            p = {'tri':tri, 'lock':lk, 'sl':sl, 'eom_sens':0.5}
            pnl = evaluate_strategy(df, p, strat)
            if pnl > best_pnl: best_pnl = pnl; best_p = p
    elif strat in ['MA_MFI_Rebound', 'MFI_MACD_Div', 'MA60_MFI', 'Range_Fade']:
        grids = itertools.product(tp_grid, sl_grid, [30, 35, 40, 45])
        for tp, sl, mfi in grids:
            p = {'tp':tp, 'sl':sl, 'mfi':mfi}
            pnl = evaluate_strategy(df, p, strat)
            if pnl > best_pnl: best_pnl = pnl; best_p = p
    elif strat == 'MFI_Extreme':
        grids = itertools.product(tp_grid, sl_grid, [20, 25, 30])
        for tp, sl, mfi_s in grids:
            p = {'tp':tp, 'sl':sl, 'mfi_s':mfi_s}
            pnl = evaluate_strategy(df, p, strat)
            if pnl > best_pnl: best_pnl = pnl; best_p = p
    elif strat in ['Dual_MA_MACD', 'MACD_Pullback']:
        grids = itertools.product(tp_grid, sl_grid, [-0.5, 0.0, 0.5])
        for tp, sl, macd in grids:
            p = {'tp':tp, 'sl':sl, 'macd':macd}
            pnl = evaluate_strategy(df, p, strat)
            if pnl > best_pnl: best_pnl = pnl; best_p = p
    elif strat == 'Vol_Breakout':
        grids = itertools.product(tp_grid, sl_grid, [0.0, 0.5, 1.0])
        for tp, sl, eom_sens in grids:
            p = {'tp':tp, 'sl':sl, 'eom_sens':eom_sens}
            pnl = evaluate_strategy(df, p, strat)
            if pnl > best_pnl: best_pnl = pnl; best_p = p
    elif strat == 'Triple_Confirm':
        grids = itertools.product(tp_grid, sl_grid, [0.0, 0.5])
        for tp, sl, eom_th in grids:
            p = {'tp':tp, 'sl':sl, 'eom_th':eom_th}
            pnl = evaluate_strategy(df, p, strat)
            if pnl > best_pnl: best_pnl = pnl; best_p = p

    best_params_db[code] = best_p
    print(f"  -> Best PnL: {best_pnl}, Params: {best_p}")

# 產生 HTML
print("建構 HTML 介面與獨立邏輯...")

html_head = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>技術分析測試-全個股深度分析版</title>
    <script src="https://cdn.jsdelivr.net/npm/xlsx/dist/xlsx.full.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root { --primary: #1e40af; --bg: #f1f5f9; --win: #dc2626; --loss: #16a34a; }
        body { font-family: 'PingFang TC', 'Microsoft JhengHei', sans-serif; background: var(--bg); margin: 0; padding: 0; color: #1e293b; }
        .nav-tabs { background: #0f172a; padding: 15px 0; display: flex; flex-wrap: wrap; justify-content: center; gap: 12px; position: sticky; top: 0; z-index: 100; }
        .tab-btn { padding: 10px 25px; border: none; background: #334155; color: white; border-radius: 8px; cursor: pointer; font-weight: bold; transition: 0.3s; }
        .tab-btn.active { background: #2563eb; box-shadow: 0 0 15px rgba(37, 99, 235, 0.4); }
        .container { max-width: 1200px; margin: 20px auto; background: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
        .page { display: none; }
        .page.active { display: block; }
        .control-panel { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; background: #f8fafc; padding: 20px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #e2e8f0; }
        .param-group { display: flex; flex-direction: column; gap: 6px; }
        .param-group label { font-size: 12px; font-weight: bold; color: #475569; }
        .param-group input, .param-group select { padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 13px; background: white; }
        .section-title { grid-column: 1 / -1; font-size: 14px; color: #1e40af; border-bottom: 1px solid #e2e8f0; padding-bottom: 5px; margin-top: 10px; font-weight: bold; }
        .drop-zone { border: 3px dashed #2563eb; padding: 25px; text-align: center; border-radius: 10px; cursor: pointer; background: #eff6ff; margin-bottom: 5px; transition: 0.3s; }
        .drop-zone:hover { background: #dbeaffe6; }
        .file-info { text-align: center; font-size: 13px; color: #1e40af; margin-bottom: 15px; font-weight: bold; }
        .dashboard { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px; }
        .stat-card { border: 1px solid #e2e8f0; padding: 12px; border-radius: 8px; text-align: center; background: #fff; }
        .stat-card b { font-size: 11px; color: #64748b; display: block; margin-bottom: 4px; }
        .stat-card span { font-size: 1.25em; font-weight: bold; }
        .win { color: var(--win); } .loss { color: var(--loss); } 
        .chart-wrap { height: 450px; margin-bottom: 25px; border: 1px solid #e2e8f0; padding: 10px; border-radius: 10px; background: white; }
        table { width: 100%; border-collapse: collapse; font-size: 13px; }
        th, td { padding: 10px; border-bottom: 1px solid #f1f5f9; text-align: center; }
        th { background: #f8fafc; position: sticky; top: 0; }
        .buy-row { background: #fff1f0; } .sell-row { background: #f0fdf4; }
    </style>
</head>
<body>
"""

nav_html = '<nav class="nav-tabs">\n'
pages_html = '<div class="container">\n'
js_vars = "let charts = {};\nlet dataStore = {};\n"
js_logic = ""

for i, (code, info) in enumerate(strategies.items()):
    name = info['name']
    strat = info['type']
    p = best_params_db.get(code, {})
    
    active_cls = ' active' if i == 0 else ''
    nav_html += f"""<button class="tab-btn{active_cls}" onclick="switchTab('tab_{code}')">{code}_{name}</button>\n"""
    
    # 建立獨立 UI 面板
    ui = ""
    logic = ""
    extract = ""
    
    if strat == 'V4':
        ui = f"""
            <div class="section-title">資金與基礎出口</div>
            <div class="param-group"><label>交易張數</label><input type="number" id="s{code}_sh" value="1"></div>
            <div class="param-group"><label>固定停利 (%)</label><input type="number" id="s{code}_tp" value="{p.get('tp',0.1)*100:.1f}" step="0.1"></div>
            <div class="param-group"><label>固定停損 (%)</label><input type="number" id="s{code}_sl" value="{p.get('sl',0.05)*100:.1f}" step="0.1"></div>
            <div class="section-title">進場過濾參數</div>
            <div class="param-group"><label>均線趨勢確認</label><select id="s{code}_ma"><option value="ma20" selected>MA 20 (月線)</option><option value="ma60">MA 60 (季線)</option></select></div>
            <div class="param-group"><label>MACD 需大於</label><input type="number" id="s{code}_macd" value="{p.get('macd',0):.1f}" step="0.1"></div>
            <div class="param-group"><label>EOM 金叉偏移</label><input type="number" id="s{code}_eom" value="{p.get('eom_off',0):.1f}" step="0.1"></div>
            <div class="param-group"><label>MFI 門檻</label><input type="number" id="s{code}_mfi" value="{p.get('mfi',40):.1f}" step="1"></div>
        """
        extract = f"let tp=parseFloat(document.getElementById('s{code}_tp').value)/100, sl=parseFloat(document.getElementById('s{code}_sl').value)/100, macd=parseFloat(document.getElementById('s{code}_macd').value), eom=parseFloat(document.getElementById('s{code}_eom').value), mfi=parseFloat(document.getElementById('s{code}_mfi').value), ma=document.getElementById('s{code}_ma').value;"
        logic = """
            let maV = ma==='ma60'?c.ma60:c.ma20;
            if(!hold){
                if(c.close > maV && c.eom > (c.eomSig + eom) && c.macd > macd && c.mfi > mfi){
                    hold=true; bp=n.open; bi[i+1]=1; mCap=Math.max(mCap, bp*sh); trd.push({type:'買入', date:n.date, price:bp, info:'V4進場'});
                }
            } else {
                let pnlR = (n.open-bp)/bp;
                if(pnlR >= tp || pnlR <= -sl){
                    hold=false; let ep=n.open; let diff=(ep-bp)*sh; tot+=diff; si[i+1]=1; trd.push({type:'賣出', date:n.date, price:ep, info:pnlR>0?'停利':'停損', pnl:diff, entP:bp});
                }
            }
        """
    elif strat == 'V38':
        ui = f"""
            <div class="section-title">資金與鎖利出口</div>
            <div class="param-group"><label>交易張數</label><input type="number" id="s{code}_sh" value="1"></div>
            <div class="param-group"><label>觸發鎖利 (%)</label><input type="number" id="s{code}_tri" value="{p.get('tri',0.03)*100:.1f}" step="0.1"></div>
            <div class="param-group"><label>保證獲利 (%)</label><input type="number" id="s{code}_lk" value="{p.get('lock',0.02)*100:.1f}" step="0.1"></div>
            <div class="param-group"><label>硬性停損 (%)</label><input type="number" id="s{code}_st" value="{p.get('sl',0.03)*100:.1f}" step="0.1"></div>
            <div class="section-title">進場過濾參數</div>
            <div class="param-group"><label>進場均線參考</label><select id="s{code}_ma"><option value="ma20" selected>MA 20 (月線)</option><option value="ma60">MA 60 (季線)</option></select></div>
            <div class="param-group"><label>EOM 金叉靈敏度</label><input type="number" id="s{code}_eom" value="{p.get('eom_sens',0.5):.1f}" step="0.1"></div>
            <div class="param-group"><label>必須突破前高</label><select id="s{code}_brk"><option value="yes" selected>是</option><option value="no">否</option></select></div>
        """
        extract = f"let tri=parseFloat(document.getElementById('s{code}_tri').value)/100, lk=parseFloat(document.getElementById('s{code}_lk').value)/100, st=parseFloat(document.getElementById('s{code}_st').value)/100, eom=parseFloat(document.getElementById('s{code}_eom').value), ma=document.getElementById('s{code}_ma').value, brk=document.getElementById('s{code}_brk').value;"
        logic = """
            let maV = ma==='ma60'?c.ma60:c.ma20;
            if(!hold){
                let eomC = c.eom > (c.eomSig + eom) && p.eom <= (p.eomSig + eom);
                let maC = c.close > maV;
                let brkC = brk==='yes'? c.close > p.high : true;
                if(eomC && maC && brkC && c.macd > p.macd){
                    hold=true; bp=n.open; bi[i+1]=1; mPrf=0; mCap=Math.max(mCap, bp*sh); trd.push({type:'買入', date:n.date, price:bp, info:'V38進場'});
                }
            } else {
                let curR=(c.close-bp)/bp; mPrf=Math.max(mPrf, curR);
                let nOpR=(n.open-bp)/bp, tP = bp*(1+lk);
                let exit=false, rsn="";
                if(mPrf>=tri && nOpR<=lk) {exit=true; rsn="獲利鎖定";}
                else if(c.eom < c.eomSig) {exit=true; rsn="動能轉弱";}
                else if(nOpR < -st) {exit=true; rsn="硬停損";}
                if(exit){
                    hold=false; let ep=(rsn==="獲利鎖定" && tP<=n.high && tP>=n.low)? tP: n.open; let diff=(ep-bp)*sh; tot+=diff; si[i+1]=1; trd.push({type:'賣出', date:n.date, price:ep, info:rsn, pnl:diff, entP:bp});
                }
            }
        """
    else:
        # 其他十種策略共享標準 UI，但參數預設值不同
        tp_v = p.get('tp', 0.1)*100; sl_v = p.get('sl', 0.05)*100
        macd_v = p.get('macd', 0); mfi_v = p.get('mfi', 40); mfi_s_v = p.get('mfi_s', 30)
        eom_v = p.get('eom_sens', 0.5) if 'eom_sens' in p else p.get('eom_th', 0.5)
        
        ui = f"""
            <div class="section-title">資金與基礎出口</div>
            <div class="param-group"><label>交易張數</label><input type="number" id="s{code}_sh" value="1"></div>
            <div class="param-group"><label>固定停利 (%)</label><input type="number" id="s{code}_tp" value="{tp_v:.1f}" step="0.1"></div>
            <div class="param-group"><label>固定停損 (%)</label><input type="number" id="s{code}_sl" value="{sl_v:.1f}" step="0.1"></div>
            <div class="section-title">進場過濾參數</div>
            <div class="param-group"><label>MACD 參數</label><input type="number" id="s{code}_macd" value="{macd_v:.1f}" step="0.1"></div>
            <div class="param-group"><label>MFI 參數</label><input type="number" id="s{code}_mfi" value="{mfi_v:.1f}" step="1"></div>
            <div class="param-group"><label>EOM 參數</label><input type="number" id="s{code}_eom" value="{eom_v:.1f}" step="0.1"></div>
        """
        extract = f"let tp=parseFloat(document.getElementById('s{code}_tp').value)/100, sl=parseFloat(document.getElementById('s{code}_sl').value)/100, macd=parseFloat(document.getElementById('s{code}_macd').value), mfi=parseFloat(document.getElementById('s{code}_mfi').value), eom=parseFloat(document.getElementById('s{code}_eom').value);"
        
        # 獨立邏輯
        entry_cond = ""
        exit_cond = "let pnlR = (n.open-bp)/bp; if(pnlR >= tp || pnlR <= -sl){ hold=false; let ep=n.open; let diff=(ep-bp)*sh; tot+=diff; si[i+1]=1; trd.push({type:'賣出', date:n.date, price:ep, info:pnlR>0?'停利':'停損', pnl:diff, entP:bp}); }"
        
        if strat == 'MA_MFI_Rebound': entry_cond = "c.close > c.ma60 && c.mfi > mfi && c.eom > c.eomSig"
        elif strat == 'Dual_MA_MACD': entry_cond = "c.close > c.ma20 && c.ma20 > c.ma60 && c.macd > macd"
        elif strat == 'EOM_Break_Lock':
            entry_cond = "c.eom > c.eomSig && p.eom <= p.eomSig && c.macd > 0"
            exit_cond = "let pnlR = (n.open-bp)/bp; if(pnlR >= tp || pnlR <= -sl || c.eom < c.eomSig){ hold=false; let ep=n.open; let diff=(ep-bp)*sh; tot+=diff; si[i+1]=1; trd.push({type:'賣出', date:n.date, price:ep, info:'出場', pnl:diff, entP:bp}); }"
        elif strat == 'MFI_Extreme': entry_cond = "c.mfi < mfi && c.close > c.ma20"
        elif strat == 'Vol_Breakout': entry_cond = "c.close > p.high && c.eom > (c.eomSig + eom) && c.mfi > 50"
        elif strat == 'MACD_Pullback': entry_cond = "c.macd > 0 && c.macd < p.macd && c.close > c.ma20"
        elif strat == 'MFI_MACD_Div': entry_cond = "c.mfi < mfi && c.macd > p.macd"
        elif strat == 'MA60_MFI': entry_cond = "c.close > c.ma60 && c.mfi < mfi"
        elif strat == 'Triple_Confirm': entry_cond = "c.close > c.ma20 && c.eom > eom && c.macd > 0"
        elif strat == 'Range_Fade': 
            entry_cond = "c.close < c.ma20 && c.mfi < mfi"
            exit_cond = "let pnlR = (n.open-bp)/bp; if(c.close > c.ma20 || pnlR >= tp || pnlR <= -sl){ hold=false; let ep=n.open; let diff=(ep-bp)*sh; tot+=diff; si[i+1]=1; trd.push({type:'賣出', date:n.date, price:ep, info:'反轉出場', pnl:diff, entP:bp}); }"

        logic = f"""
            if(!hold){{
                if({entry_cond}){{
                    hold=true; bp=n.open; bi[i+1]=1; mCap=Math.max(mCap, bp*sh); trd.push({{type:'買入', date:n.date, price:bp, info:'獨立策略進場'}});
                }}
            }} else {{
                {exit_cond}
            }}
        """

    pages_html += f"""
    <div id="tab_{code}" class="page{active_cls}">
        <h3 style="text-align:center; color:#1e40af;">{name} ({code}) 獨立策略實驗室 - {strat}</h3>
        <div class="control-panel">{ui}</div>
        <div class="drop-zone" id="s{code}_drop"><strong>將 {code} 檔案拖入此處</strong><br>策略：{strat}<input type="file" id="s{code}_file" hidden></div>
        <div id="s{code}_filename" class="file-info">未載入檔案</div>
        <div class="dashboard" id="s{code}_dash"></div>
        <div class="chart-wrap"><canvas id="s{code}_chart"></canvas></div>
        <table id="s{code}_table"><thead><tr><th>類型</th><th>日期</th><th>價格</th><th>原因</th><th>損益(元)</th></tr></thead><tbody></tbody></table>
    </div>
    """
    
    js_vars += f"charts['s{code}'] = null; dataStore['s{code}'] = null;\n"
    js_logic += f"""
document.getElementById('s{code}_drop').onclick = () => document.getElementById('s{code}_file').click();
document.getElementById('s{code}_file').onchange = (e) => {{
    if (e.target.files.length > 0) {{
        document.getElementById('s{code}_filename').innerText = "📄 已載入：" + e.target.files[0].name;
        const reader = new FileReader();
        reader.onload = (ev) => {{
            const wb = XLSX.read(ev.target.result, {{type: 'array'}});
            dataStore['s{code}'] = parseData(XLSX.utils.sheet_to_json(wb.Sheets[wb.SheetNames[0]], {{header: 1}}));
            run_s{code}();
        }};
        reader.readAsArrayBuffer(e.target.files[0]);
    }}
}};
document.querySelectorAll('#tab_{code} input, #tab_{code} select').forEach(i => i.oninput = () => dataStore['s{code}'] && run_s{code}());

function run_s{code}() {{
    const ds = dataStore['s{code}'];
    if(!ds) return;
    const sh = parseInt(document.getElementById('s{code}_sh').value) * 1000;
    {extract}
    let trd = [], hold = false, bp = 0, tot = 0, mCap = 0, mPrf = 0;
    let bi = new Array(ds.length).fill(null), si = new Array(ds.length).fill(null);

    for(let i=1; i<ds.length-1; i++){{
        let c = ds[i], n = ds[i+1], p = ds[i-1];
        {logic}
    }}
    updateUI('s{code}', trd, tot, mCap, ds, bi, si);
}}
"""

nav_html += '</nav>\n'
pages_html += '</div>\n'

html_footer = """
<script>
const verticalLinePlugin = {
    id: 'verticalLinePlugin',
    beforeDraw(chart) {
        const { ctx, chartArea: { top, bottom }, scales: { x } } = chart;
        chart.data.datasets.forEach(dataset => {
            if (dataset.lineType) {
                ctx.save(); ctx.lineWidth = 2;
                ctx.strokeStyle = dataset.lineType === 'buy' ? 'rgba(220, 38, 38, 0.6)' : 'rgba(22, 163, 74, 0.6)';
                dataset.data.forEach((val, idx) => {
                    if (val !== null) {
                        const xPos = x.getPixelForValue(chart.data.labels[idx]);
                        ctx.beginPath(); ctx.moveTo(xPos, top); ctx.lineTo(xPos, bottom); ctx.stroke();
                    }
                });
                ctx.restore();
            }
        });
    }
};
Chart.register(verticalLinePlugin);

function switchTab(target) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById(target).classList.add('active');
    event.currentTarget.classList.add('active');
}

const parseData = (rows) => {
    const p = (v) => v ? parseFloat(String(v).replace(/[↑↓,%\\s]/g, '')) || 0 : 0;
    return rows.filter(r => r[0] && (String(r[0]).includes('/') || /^\\d{8}$/.test(r[0]))).map(r => ({
        date: String(r[0]).trim(), open: p(r[1]), high: p(r[2]), low: p(r[3]), close: p(r[4]),
        ma20: p(r[8]), ma60: p(r[9]), eom: p(r[10]), eomSig: p(r[11]), mfi: p(r[12]), macd: p(r[14])
    }));
};

function updateUI(pre, trd, tot, mCap, ds, bi, si) {
    const sls = trd.filter(t => t.type === '賣出');
    const pnls = sls.map(t => t.pnl);
    const cnt = sls.length, win = pnls.filter(v => v > 0).length;
    const mxP = cnt > 0 ? Math.max(...pnls) : 0, mxL = cnt > 0 ? Math.min(...pnls) : 0;
    const avg = cnt > 0 ? tot / cnt : 0;
    const avgEnt = cnt > 0 ? (sls.reduce((sum, t) => sum + t.entP, 0) / cnt) * (parseInt(document.getElementById(pre+'_sh').value)*1000) : 1;
    const expR = (avg / avgEnt) * 100;

    document.getElementById(pre + '_dash').innerHTML = `
        <div class="stat-card"><b>累積淨損益總額</b><span class="${tot>=0?'win':'loss'}">$${Math.round(tot).toLocaleString()}</span></div>
        <div class="stat-card"><b>最大所需本金</b><span>$${Math.round(mCap).toLocaleString()}</span></div>
        <div class="stat-card"><b>真實投報率 (ROI)</b><span class="${tot>=0?'win':'loss'}">${mCap>0?(tot/mCap*100).toFixed(2):0}%</span></div>
        <div class="stat-card"><b>交易次數 / 勝率</b><span>${cnt}次 / ${cnt>0?(win/cnt*100).toFixed(1):0}%</span></div>
        <div class="stat-card"><b>單筆最大獲利</b><span class="win">$${Math.round(mxP).toLocaleString()}</span></div>
        <div class="stat-card"><b>單筆最大虧損</b><span class="loss">$${Math.round(mxL).toLocaleString()}</span></div>
        <div class="stat-card"><b>平均每筆損益</b><span class="${avg>=0?'win':'loss'}">$${Math.round(avg).toLocaleString()}</span></div>
        <div class="stat-card"><b>期望報酬率 (每筆)</b><span class="${expR>=0?'win':'loss'}">${expR.toFixed(2)}%</span></div>
    `;

    const tbody = document.querySelector(`#${pre}_table tbody`);
    tbody.innerHTML = trd.map(t => `
        <tr class="${t.type==='買入'?'buy-row':'sell-row'}">
            <td><b>${t.type}</b></td><td>${t.date}</td><td>${t.price.toFixed(1)}</td><td>${t.info}</td>
            <td class="${t.pnl>0?'win':(t.pnl<0?'loss':'')}">${t.pnl?Math.round(t.pnl).toLocaleString():'-'}</td>
        </tr>
    `).reverse().join('');

    const ctx = document.getElementById(pre + '_chart');
    if (charts[pre]) charts[pre].destroy();
    charts[pre] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ds.map(d => d.date),
            datasets: [
                { label: '收盤價', data: ds.map(d => d.close), borderColor: '#475569', borderWidth: 1, pointRadius: 0, yAxisID: 'y' },
                { data: bi, lineType: 'buy', pointRadius: 0, yAxisID: 'y_sub' },
                { data: si, lineType: 'sell', pointRadius: 0, yAxisID: 'y_sub' }
            ]
        },
        options: {
            maintainAspectRatio: false,
            scales: { y: { type: 'linear', position: 'left' }, y_sub: { display: false, min: 0, max: 1 } },
            plugins: { legend: { display: false } }
        }
    });
}
"""

with open(output_html, 'w', encoding='utf-8') as f:
    f.write(html_head + nav_html + pages_html + html_footer + js_vars + js_logic + "</script>\n</body>\n</html>")

print("分析與建構完成！新版 HTML 已經寫出。")
