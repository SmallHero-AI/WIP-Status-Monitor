import pandas as pd
import numpy as np
import itertools
import os
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import PatternFill, Font, Alignment

input_dir = "E:\\G-AI-1\\Stock analysis\\Stock original"
output_html = "E:\\G-AI-1\\Stock analysis\\技術分析測試_全個股_高勝率修正版_最終完美同步版.html"
output_dir = "E:\\G-AI-1\\Stock analysis"

strategies = {
    '2330': {'name': '台積電', 'type': 'V4_MA'},
    '3443': {'name': '創意', 'type': 'V38'},
    '2360': {'name': '致茂', 'type': 'V4'},
    '6205': {'name': '詮欣', 'type': 'V4'},
    '6669': {'name': '緯穎', 'type': 'V_Rebound'},
    '3189': {'name': '景碩', 'type': 'V_Rebound'},
    '3455': {'name': '由田', 'type': 'V_Rebound'},
    '3535': {'name': '晶彩科', 'type': 'V_Rebound'},
    '4908': {'name': '前鼎', 'type': 'V_Rebound'},
    '6269': {'name': '台郡', 'type': 'V_Rebound'},
    '4746': {'name': '台耀', 'type': 'V_Dip_Buy'},
    '6261': {'name': '久元', 'type': 'V_Dip_Buy'},
}

stock_data = {}
for file in os.listdir(input_dir):
    if file.endswith(".xlsx"):
        code = file.split('_')[0]
        if code in strategies:
            df = pd.read_excel(os.path.join(input_dir, file))
            df.columns = [str(c) for c in df.columns]
            for col in df.columns[1:]:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            stock_data[code] = {'df': df, 'file': file}

def evaluate_strategy(df, params, strat_type):
    # indicators mapping (A:0...O:14)
    close_arr, open_arr, high_arr, low_arr = df.iloc[:, 4].values, df.iloc[:, 1].values, df.iloc[:, 2].values, df.iloc[:, 3].values
    ma20_arr, ma60_arr = df.iloc[:, 7].values, df.iloc[:, 8].values
    eom_arr, eomsig_arr = df.iloc[:, 10].values, df.iloc[:, 11].values
    mfi_arr, macd_arr = df.iloc[:, 12].values, df.iloc[:, 14].values
    
    hold = False; buy_price = 0.0; pnls = []; entry_prices = []; mPrf = 0
    for i in range(1, len(df)-1):
        c_close, n_open = close_arr[i], open_arr[i+1]
        c_ma20, c_ma60 = ma20_arr[i], ma60_arr[i]
        c_eom, c_eomsig = eom_arr[i], eomsig_arr[i]
        c_mfi, c_macd = mfi_arr[i], macd_arr[i]
        p_eom, p_eomsig = eom_arr[i-1], eomsig_arr[i-1]
        p_high, p_macd = high_arr[i-1], macd_arr[i-1]
        
        if not hold:
            entry = False
            if strat_type in ['V4', 'V4_MA']:
                ma_val = ma60_arr[i] if params.get('ma_type') == 'ma60' else ma20_arr[i]
                entry = c_close > ma_val and c_eom > c_eomsig and c_macd > params['macd'] and c_mfi > params['mfi']
            elif strat_type == 'V38':
                ma_val = ma60_arr[i] if params.get('ma_type') == 'ma60' else ma20_arr[i]
                eom_cond = (c_eom > c_eomsig) and (p_eom <= p_eomsig)
                ma_cond = c_close > ma_val
                macd_cond = (c_macd > p_macd) if params.get('macd_mode') == 'grow' else (c_macd > 0 if params.get('macd_mode') == 'zero' else True)
                entry = eom_cond and ma_cond and macd_cond
            elif strat_type == 'V_Rebound':
                entry = c_close < c_ma20 and c_mfi < params['mfi_s'] and c_macd > p_macd
            elif strat_type == 'V_Dip_Buy':
                entry = c_mfi < params['mfi_s'] and c_eom > p_eom and c_macd > 0
            if entry:
                hold = True; buy_price = n_open; mPrf = 0; entry_prices.append(buy_price)
        else:
            pnlR = (n_open - buy_price) / buy_price
            curR = (c_close - buy_price) / buy_price
            mPrf = max(mPrf, curR)
            exit_flag = False; exit_price = n_open
            if strat_type == 'V38':
                tri = params['trigger']; lk = params['lock']; st = params['stop']
                if mPrf >= tri and pnlR <= lk:
                    exit_flag = True; target_p = buy_price * (1 + lk)
                    if target_p <= high_arr[i+1] and target_p >= low_arr[i+1]: exit_price = target_p
                elif c_eom < c_eomsig: exit_flag = True
                elif pnlR < -st: exit_flag = True
            elif strat_type in ['V_Rebound', 'V_Dip_Buy']:
                if c_mfi > 80 or pnlR >= params['tp'] or pnlR <= -params['sl']: exit_flag = True
            else:
                if pnlR >= params['tp'] or pnlR <= -params['sl']: exit_flag = True
            if exit_flag:
                hold = False; pnls.append((exit_price - buy_price) * 1000)
    if not pnls: return -999999, {}
    cp = sum(pnls); mc = max(entry_prices) * 1000 if entry_prices else 0
    return cp, {'累積淨損益總額': cp, '最大所需本金': mc, '勝率': len([p for p in pnls if p > 0]) / len(pnls)}

print("開始最終完美同步版建構...")
top5_db = {}
for code, info in strategies.items():
    if code not in stock_data: continue
    df = stock_data[code]['df']; strat = info['type']
    results = []
    if code == '2330': grids = [dict(tp=0.16,sl=0.09,macd=5.3,mfi=30,ma_type='ma20')]
    elif code == '3443': grids = [dict(trigger=0.025, lock=0.035, stop=0.03, ma_type='ma60', macd_mode='zero')]
    elif strat == 'V4': grids = [dict(tp=0.189,sl=0.08,macd=2.1,mfi=30)]
    elif strat == 'V_Rebound': grids = [dict(tp=0.1,sl=0.06,mfi_s=30)]
    else: grids = [dict(tp=0.1,sl=0.05,mfi_s=30)]
    for p in grids:
        pnl, stat = evaluate_strategy(df, p, strat)
        if pnl > -999999: res = p.copy(); res.update(stat); results.append(res)
    top5_db[code] = pd.DataFrame(results)

# 組裝 HTML
html_start = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>技術分析測試-完美同步最終版</title>
    <script src="https://cdn.jsdelivr.net/npm/xlsx/dist/xlsx.full.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root { --primary: #1e40af; --bg: #f1f5f9; --win: #dc2626; --loss: #16a34a; }
        body { font-family: sans-serif; background: var(--bg); margin: 0; padding: 0; color: #1e293b; }
        .nav-tabs { background: #0f172a; padding: 10px; display: flex; flex-wrap: wrap; justify-content: center; gap: 8px; position: sticky; top: 0; z-index: 1000; }
        .tab-btn { padding: 8px 16px; border: none; background: #334155; color: white; border-radius: 6px; cursor: pointer; font-weight: bold; }
        .tab-btn.active { background: #2563eb; }
        .container { max-width: 1200px; margin: 20px auto; background: white; padding: 20px; border-radius: 12px; }
        .page { display: none; } .page.active { display: block; }
        .control-panel { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 10px; background: #f8fafc; padding: 15px; border-radius: 8px; margin-bottom: 15px; border: 1px solid #e2e8f0; }
        .param-group { display: flex; flex-direction: column; gap: 4px; }
        .param-group label { font-size: 11px; font-weight: bold; }
        .param-group input, .param-group select { padding: 6px; border: 1px solid #cbd5e1; border-radius: 4px; font-size: 12px; }
        .section-title { grid-column: 1 / -1; font-size: 12px; color: #1e40af; border-bottom: 1px solid #e2e8f0; margin-top: 10px; font-weight: bold; }
        .drop-zone { border: 2px dashed #2563eb; padding: 30px; text-align: center; border-radius: 8px; cursor: pointer; background: #eff6ff; margin-bottom: 20px; }
        .dashboard { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 20px; }
        .stat-card { border: 1px solid #e2e8f0; padding: 10px; border-radius: 6px; text-align: center; }
        .stat-card b { font-size: 10px; color: #64748b; display: block; }
        .stat-card span { font-size: 1.1em; font-weight: bold; }
        .win { color: var(--win); } .loss { color: var(--loss); } 
        .chart-wrap { height: 400px; margin-bottom: 20px; border: 1px solid #e2e8f0; }
        table { width: 100%; border-collapse: collapse; font-size: 12px; }
        th, td { padding: 8px; border-bottom: 1px solid #f1f5f9; text-align: center; }
        .buy-row { background: #fff1f0; } .sell-row { background: #f0fdf4; }
    </style>
</head>
<body>
<nav class="nav-tabs">
"""

nav_html = ""; pages_html = ""; js_logic = ""
for i, (code, info) in enumerate(strategies.items()):
    strat = info['type']; name = info['name']; top5 = top5_db.get(code)
    p = top5.iloc[0] if top5 is not None and not top5.empty else {}
    nav_html += f'<button class="tab-btn{" active" if i==0 else ""}" onclick="switchTab(event, \'tab_{code}\')">{code}_{name}</button>\n'
    
    ui = ""
    if strat in ['V4', 'V4_MA']:
        ui = f"""<div class="section-title">資金與基礎出口</div>
        <div class="param-group"><label>張數</label><input type="number" id="s{code}_sh" value="1"></div>
        <div class="param-group"><label>停利 (%)</label><input type="number" id="s{code}_tp" value="{p.get('tp',0)*100:.1f}"></div>
        <div class="param-group"><label>停損 (%)</label><input type="number" id="s{code}_sl" value="{p.get('sl',0)*100:.1f}"></div>
        <div class="section-title">進場過濾</div>
        <div class="param-group"><label>均線</label><select id="s{code}_ma"><option value="ma20" {"selected" if p.get('ma_type')=='ma20' else ""}>MA20</option><option value="ma60" {"selected" if p.get('ma_type')=='ma60' else ""}>MA60</option></select></div>
        <div class="param-group"><label>MACD ></label><input type="number" id="s{code}_macd" value="{p.get('macd',0)}"></div>
        <div class="param-group"><label>MFI ></label><input type="number" id="s{code}_mfi" value="{p.get('mfi',0)}"></div>"""
    elif strat == 'V38':
        ui = f"""<div class="section-title">鎖利出口</div>
        <div class="param-group"><label>張數</label><input type="number" id="s{code}_sh" value="1"></div>
        <div class="param-group"><label>觸發鎖利</label><input type="number" id="s{code}_tri" value="{p.get('trigger',0)*100:.1f}"></div>
        <div class="param-group"><label>保證獲利</label><input type="number" id="s{code}_lk" value="{p.get('lock',0)*100:.1f}"></div>
        <div class="param-group"><label>硬性停損</label><input type="number" id="s{code}_st" value="{p.get('stop',0)*100:.1f}"></div>
        <div class="section-title">進場過濾</div>
        <div class="param-group"><label>均線</label><select id="s{code}_ma"><option value="ma20">MA20</option><option value="ma60" selected>MA60</option></select></div>"""

    pages_html += f"""<div id="tab_{code}" class="page{" active" if i==0 else ""}"><div class="container">
    <h3 style="text-align:center;">{name} ({code}) - {strat}</h3>
    <div class="control-panel">{ui}</div>
    <div class="drop-zone" id="s{code}_drop">將 {code} 檔案拖入此處或點擊上傳</div>
    <div id="s{code}_dash" class="dashboard"></div>
    <div class="chart-wrap"><canvas id="s{code}_chart"></canvas></div>
    <table id="s{code}_table"><thead><tr><th>類型</th><th>日期</th><th>價格</th><th>原因</th><th>損益</th></tr></thead><tbody></tbody></table>
    </div></div>"""

    js_logic += f"""
    try {{
        const btn = document.getElementById('s{code}_drop');
        if(btn) btn.onclick = () => {{
            const inp = document.createElement('input'); inp.type='file';
            inp.onchange=(e)=>{{
                const f=e.target.files[0]; if(!f) return;
                const r=new FileReader(); r.onload=(ev)=>{{
                    const wb=XLSX.read(ev.target.result,{{type:'array'}});
                    window.dataStore['{code}'] = parseData(XLSX.utils.sheet_to_json(wb.Sheets[wb.SheetNames[0]],{{header:1}}));
                    run_{code}();
                }}; r.readAsArrayBuffer(f);
            }}; inp.click();
        }};
        window.run_{code} = () => {{
            const ds = window.dataStore['{code}']; if(!ds) return;
            const sh = parseInt(document.getElementById('s{code}_sh').value)*1000;
            // logic extraction here
            let trd=[], hold=false, bp=0, tot=0, mCap=0, mPrf=0;
            let bi=new Array(ds.length).fill(null), si=new Array(ds.length).fill(null);
            for(let i=1; i<ds.length-1; i++){{
                let c=ds[i], n=ds[i+1], p=ds[i-1];
                {"let maV=(document.getElementById('s"+code+"_ma').value==='ma60'?c.ma60:c.ma20); let tp=parseFloat(document.getElementById('s"+code+"_tp').value)/100, sl=parseFloat(document.getElementById('s"+code+"_sl').value)/100, macd=parseFloat(document.getElementById('s"+code+"_macd').value), mfi=parseFloat(document.getElementById('s"+code+"_mfi').value); if(!hold){ if(c.close>maV && c.eom>c.eomSig && c.macd>macd && c.mfi>mfi){ hold=true; bp=n.open; bi[i+1]=1; mCap=Math.max(mCap,bp*sh); trd.push({type:'買入',date:n.date,price:bp,info:'V4進場'}); } } else { let pnlR=(n.open-bp)/bp; if(pnlR>=tp || pnlR<=-sl){ hold=false; let ep=n.open; let d=(ep-bp)*sh; tot+=d; si[i+1]=1; trd.push({type:'賣出',date:n.date,price:ep,info:pnlR>0?'停利':'停損',pnl:d,entP:bp}); } }" if strat in ['V4','V4_MA'] else "let tri=parseFloat(document.getElementById('s"+code+"_tri').value)/100, lk=parseFloat(document.getElementById('s"+code+"_lk').value)/100, st=parseFloat(document.getElementById('s"+code+"_st').value)/100; if(!hold){ if(c.eom>c.eomSig && p.eom<=p.eomSig && c.close>c.ma60 && c.macd>0){ hold=true; bp=n.open; bi[i+1]=1; mPrf=0; mCap=Math.max(mCap,bp*sh); trd.push({type:'買入',date:n.date,price:bp,info:'V38進場'}); } } else { let curR=(c.close-bp)/bp; mPrf=Math.max(mPrf,curR); let nOpenR=(n.open-bp)/bp; let exit=false, rsn=''; if(mPrf>=tri && nOpenR<=lk){ exit=true; rsn='獲利鎖定'; } else if(c.eom<c.eomSig){ exit=true; rsn='動能轉弱'; } else if(nOpenR<-st){ exit=true; rsn='硬停損'; } if(exit){ hold=false; let tpP=bp*(1+lk); let ep=(rsn==='獲利鎖定' && tpP<=n.high && tpP>=n.low)?tpP:n.open; let d=(ep-bp)*sh; tot+=d; si[i+1]=1; trd.push({type:'賣出',date:n.date,price:ep,info:rsn,pnl:d,entP:bp}); } }"}
            }}
            updateUI('{code}', trd, tot, mCap, ds, bi, si);
        }};
        document.querySelectorAll('#tab_{code} input, #tab_{code} select').forEach(el=>{{ el.oninput=()=>window.run_{code}(); }});
    }} catch(e) {{ console.error(e); }}
    """

with open(output_html, 'w', encoding='utf-8') as f:
    f.write(html_start + nav_html + "</nav>\n" + pages_html + """
<script>
window.dataStore = {}; window.charts = {};
const p=(v)=>v?parseFloat(String(v).replace(/[↑↓,%\\s]/g,''))||0:0;
function switchTab(e, id) {
    document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active'));
    document.getElementById(id).classList.add('active');
    e.currentTarget.classList.add('active');
}
const parseData=(rows)=>rows.filter(r=>r[0]&&(String(r[0]).includes('/')||/^\\d{8}$/.test(r[0]))).map(r=>({
    date:String(r[0]).trim(), open:p(r[1]), high:p(r[2]), low:p(r[3]), close:p(r[4]),
    ma20:p(r[7]), ma60:p(r[8]), eom:p(r[10]), eomSig:p(r[11]), mfi:p(r[12]), macd:p(r[14])
}));
function updateUI(code, trd, tot, mCap, ds, bi, si) {
    const sls=trd.filter(t=>t.type==='賣出'), pnls=sls.map(t=>t.pnl), cnt=sls.length;
    const win=pnls.filter(v=>v>0).length, mxP=cnt?Math.max(...pnls):0, mxL=cnt?Math.min(...pnls):0, avg=cnt?tot/cnt:0;
    document.getElementById('s'+code+'_dash').innerHTML = `<div class="stat-card"><b>累積淨損益</b><span class="${tot>=0?'win':'loss'}">$${Math.round(tot).toLocaleString()}</span></div><div class="stat-card"><b>所需本金</b><span>$${Math.round(mCap).toLocaleString()}</span></div><div class="stat-card"><b>勝率</b><span>${cnt}次/${cnt>0?(win/cnt*100).toFixed(1):0}%</span></div><div class="stat-card"><b>平均損益</b><span>$${Math.round(avg).toLocaleString()}</span></div>`;
    document.querySelector('#s'+code+'_table tbody').innerHTML = trd.map(t=>`<tr class="${t.type==='買入'?'buy-row':'sell-row'}"><td><b>${t.type}</b></td><td>${t.date}</td><td>${t.price.toFixed(1)}</td><td>${t.info}</td><td class="${t.pnl>0?'win':(t.pnl<0?'loss':'')}">${t.pnl?Math.round(t.pnl).toLocaleString():'-'}</td></tr>`).reverse().join('');
    const ctx=document.getElementById('s'+code+'_chart'); if(window.charts[code]) window.charts[code].destroy();
    window.charts[code]=new Chart(ctx,{type:'line',data:{labels:ds.map(d=>d.date),datasets:[{label:'收盤',data:ds.map(d=>d.close),borderColor:'#475569',borderWidth:1,pointRadius:0},{label:'買',data:bi.map((v,i)=>v?ds[i].close:null),backgroundColor:'red',pointRadius:4,showLine:false},{label:'賣',data:si.map((v,i)=>v?ds[i].close:null),backgroundColor:'green',pointRadius:4,showLine:false}]},options:{maintainAspectRatio:false,plugins:{legend:{display:false}}}});
}
window.onload = () => {
""" + js_logic + "\n};\n</script></body></html>")

print("全自動優化建構與最終完美同步版 HTML 完成！")
