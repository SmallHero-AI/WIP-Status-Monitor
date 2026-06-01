import os
import re

html_path = "E:\\G-AI-1\\Stock analysis\\技術分析測試.html"
output_path = "E:\\G-AI-1\\Stock analysis\\全個股獨立策略測試.html"

with open(html_path, 'r', encoding='utf-8') as f:
    html_content = f.read()

stocks = {
    '2330': {'name': '台積電', 'strat': 1},
    '2360': {'name': '致茂', 'strat': 1},
    '6669': {'name': '緯穎', 'strat': 1},
    '3443': {'name': '創意', 'strat': 2},
    '3455': {'name': '由田', 'strat': 2},
    '3535': {'name': '晶彩科', 'strat': 2},
    '4746': {'name': '台耀', 'strat': 2},
    '4908': {'name': '前鼎', 'strat': 2},
    '3189': {'name': '景碩', 'strat': 3},
    '6205': {'name': '詮欣', 'strat': 3},
    '6261': {'name': '久元', 'strat': 3},
    '6269': {'name': '台郡', 'strat': 3}
}

nav_buttons = ""
pages_html = ""
js_variables = ""
js_functions = ""

for code, info in stocks.items():
    name = info['name']
    strat = info['strat']
    prefix = f"s{code}"
    
    # 1. Nav button
    nav_buttons += f"""    <button class="tab-btn" onclick="switchTab('tab_{code}')">{code}_{name}</button>\n"""
    
    # 2. HTML Page
    if strat == 1:
        strat_title = "穩健均線順勢策略 (適合權值與長線穩健股)"
        ui_params = f"""
            <div class="param-group"><label>固定停利 (%)</label><input type="number" id="{prefix}_tp" value="12" step="1"></div>
            <div class="param-group"><label>固定停損 (%)</label><input type="number" id="{prefix}_sl" value="6" step="1"></div>
            <div class="param-group"><label>MACD 需大於</label><input type="number" id="{prefix}_macd" value="0" step="0.1"></div>
        """
        logic_code = f"""
        if(!hold){{
            if(c.close > c.ma20 && c.macd > macdTh){{
                hold = true; bp = n.open; bi[i+1] = 1; mCap = Math.max(mCap, bp * sh);
                trd.push({{ type:'買入', date:n.date, price:bp, info: `均線順勢進場` }});
            }}
        }} else {{
            let pnlR = (n.open - bp)/bp;
            if(pnlR >= tp || pnlR <= -sl){{
                hold = false; let ep = n.open; let p = (ep - bp) * sh; tot += p; si[i+1] = 1;
                trd.push({{ type:'賣出', date:n.date, price:ep, info: pnlR>0?'停利':'停損', pnl:p, entP: bp }});
            }}
        }}"""
        js_params_extract = f"""
    const tp = parseFloat(document.getElementById('{prefix}_tp').value)/100;
    const sl = parseFloat(document.getElementById('{prefix}_sl').value)/100;
    const macdTh = parseFloat(document.getElementById('{prefix}_macd').value);"""

    elif strat == 2:
        strat_title = "高波動動能爆發策略 (適合強勢突破股)"
        ui_params = f"""
            <div class="param-group"><label>固定停利 (%)</label><input type="number" id="{prefix}_tp" value="20" step="1"></div>
            <div class="param-group"><label>固定停損 (%)</label><input type="number" id="{prefix}_sl" value="8" step="1"></div>
            <div class="param-group"><label>MACD 需大於</label><input type="number" id="{prefix}_macd" value="0" step="0.1"></div>
        """
        logic_code = f"""
        if(!hold){{
            if(c.close > c.ma60 && c.eom > c.eomSig && c.macd > macdTh){{
                hold = true; bp = n.open; bi[i+1] = 1; mCap = Math.max(mCap, bp * sh);
                trd.push({{ type:'買入', date:n.date, price:bp, info: `動能爆發進場` }});
            }}
        }} else {{
            let pnlR = (n.open - bp)/bp;
            let exitRsn = "";
            if(pnlR >= tp) exitRsn = "停利";
            else if(pnlR <= -sl) exitRsn = "停損";
            else if(c.eom < c.eomSig) exitRsn = "動能衰退";
            
            if(exitRsn !== ""){{
                hold = false; let ep = n.open; let p = (ep - bp) * sh; tot += p; si[i+1] = 1;
                trd.push({{ type:'賣出', date:n.date, price:ep, info: exitRsn, pnl:p, entP: bp }});
            }}
        }}"""
        js_params_extract = f"""
    const tp = parseFloat(document.getElementById('{prefix}_tp').value)/100;
    const sl = parseFloat(document.getElementById('{prefix}_sl').value)/100;
    const macdTh = parseFloat(document.getElementById('{prefix}_macd').value);"""

    elif strat == 3:
        strat_title = "波段反轉低接策略 (適合區間震盪與循環股)"
        ui_params = f"""
            <div class="param-group"><label>固定停利 (%)</label><input type="number" id="{prefix}_tp" value="12" step="1"></div>
            <div class="param-group"><label>固定停損 (%)</label><input type="number" id="{prefix}_sl" value="6" step="1"></div>
            <div class="param-group"><label>MFI 超賣區</label><input type="number" id="{prefix}_mfi_s" value="40" step="1"></div>
            <div class="param-group"><label>MFI 超買區</label><input type="number" id="{prefix}_mfi_b" value="80" step="1"></div>
        """
        logic_code = f"""
        if(!hold){{
            if(c.close > c.ma20 && c.mfi < mfiS){{
                hold = true; bp = n.open; bi[i+1] = 1; mCap = Math.max(mCap, bp * sh);
                trd.push({{ type:'買入', date:n.date, price:bp, info: `低接反轉進場` }});
            }}
        }} else {{
            let pnlR = (n.open - bp)/bp;
            let exitRsn = "";
            if(pnlR >= tp) exitRsn = "停利";
            else if(pnlR <= -sl) exitRsn = "停損";
            else if(c.mfi > mfiB) exitRsn = "超買過熱";
            
            if(exitRsn !== ""){{
                hold = false; let ep = n.open; let p = (ep - bp) * sh; tot += p; si[i+1] = 1;
                trd.push({{ type:'賣出', date:n.date, price:ep, info: exitRsn, pnl:p, entP: bp }});
            }}
        }}"""
        js_params_extract = f"""
    const tp = parseFloat(document.getElementById('{prefix}_tp').value)/100;
    const sl = parseFloat(document.getElementById('{prefix}_sl').value)/100;
    const mfiS = parseFloat(document.getElementById('{prefix}_mfi_s').value);
    const mfiB = parseFloat(document.getElementById('{prefix}_mfi_b').value);"""
    
    # 組合 Page HTML
    pages_html += f"""
    <div id="tab_{code}" class="page">
        <h3 style="text-align:center; color:#1e40af;">{name} ({code}) - {strat_title}</h3>
        <div class="control-panel">
            <div class="section-title">獨立策略參數設定</div>
            <div class="param-group"><label>交易張數</label><input type="number" id="{prefix}_shares" value="1"></div>
            {ui_params}
        </div>
        <div class="drop-zone" id="{prefix}_drop"><strong>將 {code} 檔案拖入此處</strong><br>支援獨立策略載入<input type="file" id="{prefix}_file" hidden></div>
        <div id="{prefix}_filename" class="file-info">未載入檔案</div>
        
        <div class="dashboard" id="{prefix}_dash"></div>
        <div class="chart-wrap"><canvas id="{prefix}_chart"></canvas></div>
        <table id="{prefix}_table"><thead><tr><th>類型</th><th>日期</th><th>價格</th><th>原因</th><th>損益(元)</th></tr></thead><tbody></tbody></table>
    </div>
"""
    
    # 組合 JS
    js_variables += f"charts['{prefix}'] = null; dataStore['{prefix}'] = null;\n"
    
    js_functions += f"""
document.getElementById('{prefix}_drop').onclick = () => document.getElementById('{prefix}_file').click();
document.getElementById('{prefix}_file').onchange = (e) => {{
    if (e.target.files.length > 0) {{
        document.getElementById('{prefix}_filename').innerText = "📄 已載入：" + e.target.files[0].name;
        const reader = new FileReader();
        reader.onload = (ev) => {{
            const wb = XLSX.read(ev.target.result, {{type: 'array'}});
            dataStore['{prefix}'] = parseData(XLSX.utils.sheet_to_json(wb.Sheets[wb.SheetNames[0]], {{header: 1}}));
            run_{prefix}();
        }};
        reader.readAsArrayBuffer(e.target.files[0]);
    }}
}};
document.querySelectorAll('#tab_{code} input, #tab_{code} select').forEach(i => i.oninput = () => dataStore['{prefix}'] && run_{prefix}());

function run_{prefix}() {{
    const ds = dataStore['{prefix}'];
    if(!ds) return;
    const sh = parseInt(document.getElementById('{prefix}_shares').value) * 1000;
    {js_params_extract}

    let trd = [], hold = false, bp = 0, tot = 0, mCap = 0;
    let bi = new Array(ds.length).fill(null), si = new Array(ds.length).fill(null);

    for(let i=1; i<ds.length-1; i++){{
        let c = ds[i], n = ds[i+1];
        {logic_code}
    }}
    updateUI('{prefix}', trd, tot, mCap, ds, bi, si);
}}
"""

# 取代原始 HTML 的 Nav、Page 和 JS 區塊
# 1. Nav
html_content = re.sub(r'<nav class="nav-tabs">.*?</nav>', f'<nav class="nav-tabs" style="flex-wrap: wrap;">\n{nav_buttons}</nav>', html_content, flags=re.DOTALL)

# 2. Pages
# 找到 <div class="container"> 到 </div> 結尾
start_idx = html_content.find('<div class="container">') + len('<div class="container">')
end_idx = html_content.find('</div>\n\n<script>')
html_content = html_content[:start_idx] + "\n" + pages_html + html_content[end_idx:]

# 3. JS (刪除舊的 TSMC / GUC，加上新的)
# 找到 let charts = { t: null, g: null };
html_content = re.sub(r"let charts = \{.*?\};", "let charts = {};", html_content)
html_content = re.sub(r"let dataStore = \{.*?\};", "let dataStore = {};\n" + js_variables, html_content)

# 找到 // --- TSMC 邏輯 --- 並砍掉直到 updateUI 之前
tsmc_start = html_content.find('// --- TSMC 邏輯 ---')
updateui_start = html_content.find('function updateUI(pre')
html_content = html_content[:tsmc_start] + js_functions + "\n" + html_content[updateui_start:]

# 寫出檔案
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

print("生成完成！")
