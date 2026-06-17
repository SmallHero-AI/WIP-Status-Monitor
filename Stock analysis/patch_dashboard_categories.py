# -*- coding: utf-8 -*-
import json
import os

SCRIPT_DIR = r"E:\G-AI-1\Stock analysis"
HTML_BASE_PATH = os.path.join(SCRIPT_DIR, "修正版_V6_Server", "public", "dashboard_v6_backup.html")
HTML_OUT_PATH = os.path.join(SCRIPT_DIR, "修正版_V6_Server", "public", "dashboard_v6.html")
SERVER_PATH = os.path.join(SCRIPT_DIR, "修正版_V6_Server", "server.js")
LEADERBOARD_PATH = os.path.join(SCRIPT_DIR, "修正版_V6_Server", "public", "leaderboard.json")

def main():
    print("=" * 60)
    print("  AI 策略分類與網頁重導向補丁啟動...")
    print("=" * 60)

    if not os.path.exists(LEADERBOARD_PATH):
        print("[錯誤] leaderboard.json 不存在！")
        return

    with open(LEADERBOARD_PATH, 'r', encoding='utf-8') as f:
        leaderboard = json.load(f)

    # 篩選勝率 >= 70% 的股票
    high_win = [x for x in leaderboard if x['winRate'] >= 70]
    print(f"[資訊] 共讀取到 {len(high_win)} 檔高勝率個股")

    # 分類策略定義
    trend_indicators = [
        "強勢均線多頭+KD金叉", "中長期多頭+RSI低檔轉強", "雙重均線突破+MACD翻紅", 
        "EOM動能突破+均線多頭", "突破阻力(R1)+MACD多頭", "突破樞軸(Pivot)+RSI轉強", 
        "多頭拉回：MA60之上+KD金叉+RSI<45", "動能共振：EOM突破+MACD>0+RSI>50", 
        "壓力突破：價格>R1+EOM強勢+MACD>0", "長期均線支撐：站上MA120+KD金叉+CCI超賣"
    ]
    rebound_indicators = ["雙重超賣 (RSI+CCI)+MACD轉強", "CCI超賣+MFI超賣+KD金叉"]
    oversold_indicators = ["雙保險超跌：BIAS超賣+布林下軌觸及", "極度超跌共振 (BIAS+RSI+MFI)"]
    support_indicators = ["樞軸點(S1)支撐+KD金叉", "S1支撐不破+MACD紅柱增長", "布林中軌支撐+MACD紅柱", "CCI超賣反彈+MACD紅柱增長"]

    new_stocks = []
    new_xlsx = {}

    for item in high_win:
        code = item['code']
        name = item['name']
        strategy_full = item['strategy']
        parts = strategy_full.split(' & ')
        entry = parts[0].strip()
        exit_cond = parts[1].strip()

        # 分類判斷
        strat_cat = 'ai_trend'
        if entry in trend_indicators:
            strat_cat = 'ai_trend'
        elif entry in rebound_indicators:
            strat_cat = 'ai_rebound'
        elif entry in oversold_indicators:
            strat_cat = 'ai_oversold'
        elif entry in support_indicators:
            strat_cat = 'ai_support'
        else:
            # 預設落入趨勢類
            strat_cat = 'ai_trend'

        tp = 0.0
        sl = 0.0
        if "6%停利 / 6%停損" in exit_cond:
            tp, sl = 6.0, 6.0
        elif "8%停利 / 8%停損" in exit_cond:
            tp, sl = 8.0, 8.0
        elif "12%停利 / 6%停損" in exit_cond:
            tp, sl = 12.0, 6.0
        elif "KD死叉離場或6%停損" in exit_cond:
            sl = 6.0
        elif "RSI超買離場或6%停損" in exit_cond:
            sl = 6.0
        elif "MACD紅柱縮短離場或6%停損" in exit_cond:
            sl = 6.0
        elif "收盤跌破MA20或6%停損" in exit_cond:
            sl = 6.0
        elif "觸碰布林上軌停利或6%停損" in exit_cond:
            sl = 6.0
        elif "跌破樞軸支撐(S1)或8%停利" in exit_cond:
            tp = 8.0

        new_stocks.append({
            'id': f's{code}_ai',
            'name': name,
            'strategy': strat_cat,
            'filename': f'{code}_{name}_AI_高勝率回測.xlsx',
            'entry': entry,
            'exit': exit_cond,
            'tp': tp,
            'sl': sl
        })
        new_xlsx[f's{code}_ai'] = f'{code}_{name}_AI_高勝率回測.xlsx'

    # 原本的 12 支預設個股
    base_stocks = [
        { 'id': 's2330', 'name': '台積電', 'strategy': 'v4', 'filename': '2330_台積電_V4_高勝率回測.xlsx' },
        { 'id': 's2360', 'name': '致茂', 'strategy': 'v4', 'filename': '2360_致茂_V4_高勝率回測.xlsx' },
        { 'id': 's6205', 'name': '詮欣', 'strategy': 'v4', 'filename': '6205_詮欣_V4_高勝率回測.xlsx' },
        { 'id': 's6274', 'name': '台耀', 'strategy': 'v4', 'filename': '6274_台耀_V4_高勝率回測.xlsx' },
        { 'id': 's6669', 'name': '緯穎', 'strategy': 'rebound', 'filename': '6669_緯穎_V_Rebound_高勝率回測.xlsx' },
        { 'id': 's3189', 'name': '景碩', 'strategy': 'rebound', 'filename': '3189_景碩_V_Rebound_高勝率回測.xlsx' },
        { 'id': 's3455', 'name': '由田', 'strategy': 'rebound', 'filename': '3455_由田_V_Rebound_高勝率回測.xlsx' },
        { 'id': 's3535', 'name': '晶彩科', 'strategy': 'rebound', 'filename': '3535_晶彩科_V_Rebound_高勝率回測.xlsx' },
        { 'id': 's4908', 'name': '前鼎', 'strategy': 'rebound', 'filename': '4908_前鼎_V_Rebound_高勝率回測.xlsx' },
        { 'id': 's6269', 'name': '台郡', 'strategy': 'rebound', 'filename': '6269_台郡_V_Rebound_高勝率回測.xlsx' },
        { 'id': 's3443', 'name': '創意', 'strategy': 'v38', 'filename': '3443_創意_V_Rebound_高勝率回測.xlsx' },
        { 'id': 's6261', 'name': '久元', 'strategy': 'dipbuy', 'filename': '6261_久元_V_Dip_Buy_高勝率回測.xlsx' }
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

    # 讀取備份 HTML 檔案作為全新基礎，防止重複取代導致毀損
    if not os.path.exists(HTML_BASE_PATH):
        print(f"[警告] 找不到備份 {HTML_BASE_PATH}，將使用當前 {HTML_OUT_PATH} 作為基礎。")
        with open(HTML_OUT_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        with open(HTML_BASE_PATH, 'r', encoding='utf-8') as f:
            content = f.read()

    # ── 1. 注入 presets 與新 preloadedStocks 與 xlsxFiles ──
    stocks_js = json.dumps(all_stocks, indent=8, ensure_ascii=False)
    xlsx_js = json.dumps(base_xlsx, indent=8, ensure_ascii=False)

    presets_target = 'const strategyPresets = {'
    presets_replace = """const strategyPresets = {
            ai_trend: { sh: 1, tp: 6.0, sl: 6.0 },
            ai_rebound: { sh: 1, tp: 6.0, sl: 6.0 },
            ai_oversold: { sh: 1, tp: 6.0, sl: 6.0 },
            ai_support: { sh: 1, tp: 6.0, sl: 6.0 },"""
    content = content.replace(presets_target, presets_replace)

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

    # ── 2. 側邊欄分類 Folder HTML 注入 ──
    v38_target_end = 'id="contents_v38"></div>\n            </div>'
    categories_folder_html = """\n
            <!-- AI Trend Folder -->
            <div class="strategy-folder" id="folder_ai_trend">
                <div class="folder-header" onclick="toggleFolder('ai_trend')">
                    <div class="folder-title">
                        <span class="folder-icon">▼</span>
                        <span>📁 AI 趨勢順勢策略 - 穩定版</span>
                    </div>
                    <div class="folder-actions">
                        <span class="lock-icon" style="display:none; font-size:0.8rem;">🔒</span>
                        <button class="btn-add-stock" onclick="triggerFolderUpload(event, 'ai_trend')">➕ 載入</button>
                    </div>
                </div>
                <div class="folder-contents" id="contents_ai_trend"></div>
            </div>

            <!-- AI Rebound Folder -->
            <div class="strategy-folder" id="folder_ai_rebound">
                <div class="folder-header" onclick="toggleFolder('ai_rebound')">
                    <div class="folder-title">
                        <span class="folder-icon">▼</span>
                        <span>📁 AI 超跌反彈策略 - 穩定版</span>
                    </div>
                    <div class="folder-actions">
                        <span class="lock-icon" style="display:none; font-size:0.8rem;">🔒</span>
                        <button class="btn-add-stock" onclick="triggerFolderUpload(event, 'ai_rebound')">➕ 載入</button>
                    </div>
                </div>
                <div class="folder-contents" id="contents_ai_rebound"></div>
            </div>

            <!-- AI Oversold Folder -->
            <div class="strategy-folder" id="folder_ai_oversold">
                <div class="folder-header" onclick="toggleFolder('ai_oversold')">
                    <div class="folder-title">
                        <span class="folder-icon">▼</span>
                        <span>📁 AI 極值超跌策略 - 穩定版</span>
                    </div>
                    <div class="folder-actions">
                        <span class="lock-icon" style="display:none; font-size:0.8rem;">🔒</span>
                        <button class="btn-add-stock" onclick="triggerFolderUpload(event, 'ai_oversold')">➕ 載入</button>
                    </div>
                </div>
                <div class="folder-contents" id="contents_ai_oversold"></div>
            </div>

            <!-- AI Support Folder -->
            <div class="strategy-folder" id="folder_ai_support">
                <div class="folder-header" onclick="toggleFolder('ai_support')">
                    <div class="folder-title">
                        <span class="folder-icon">▼</span>
                        <span>📁 AI 支撐反彈策略 - 穩定版</span>
                    </div>
                    <div class="folder-actions">
                        <span class="lock-icon" style="display:none; font-size:0.8rem;">🔒</span>
                        <button class="btn-add-stock" onclick="triggerFolderUpload(event, 'ai_support')">➕ 載入</button>
                    </div>
                </div>
                <div class="folder-contents" id="contents_ai_support"></div>
            </div>"""

    if v38_target_end in content:
        content = content.replace(v38_target_end, v38_target_end + categories_folder_html)
        print("  [成功] 注入 AI 分類 Folders HTML")
    else:
        v38_fallback = 'id="contents_v38"></div>'
        if v38_fallback in content:
            content = content.replace(v38_fallback, v38_fallback + '\n            </div>' + categories_folder_html)
            print("  [成功] 注入 AI 分類 Folders HTML (降級模式)")

    # ── 3. renderSidebarStocks 更新 ──
    render_target = "document.getElementById('contents_v38').innerHTML = '';"
    render_replace = """document.getElementById('contents_v38').innerHTML = '';
            ['ai_trend', 'ai_rebound', 'ai_oversold', 'ai_support'].forEach(f => {
                const el = document.getElementById('contents_' + f);
                if (el) el.innerHTML = '';
            });"""
    content = content.replace(render_target, render_replace)
    print("  [成功] 更新 renderSidebarStocks")

    # ── 4. selectStockTab 更新 ──
    select_tab_page_check_target = """                // 自訂頁面若不存在則動態生成其 V2 DOM 結構
                if (type === 'custom' && !document.getElementById(pageId)) {
                    createCustomStockPage(uniqueId, code, name, strategy);
                }"""
    select_tab_page_check_replace = """                // 所有個股頁面若不存在則動態生成其 V2 DOM 結構 (新 preloads 無需硬編碼 HTML)
                if (!document.getElementById(pageId)) {
                    createCustomStockPage(uniqueId, code, name, strategy);
                }"""
    content = content.replace(select_tab_page_check_target, select_tab_page_check_replace)

    select_tab_run_target = """                // 執行回測
                if (dataStore[uniqueId]) {
                    if (type === 'preload') {
                        window['run_' + code]();
                    } else {"""
    select_tab_run_replace = """                // 執行回測
                if (dataStore[uniqueId]) {
                    if (strategy.startsWith('ai_')) {
                        run_AI(uniqueId);
                    } else if (type === 'preload') {
                        if (typeof window['run_' + code] === 'function') {
                            window['run_' + code]();
                        } else {
                            if (strategy === 'v4') run_V4(uniqueId);
                            else if (strategy === 'rebound') run_Rebound(uniqueId);
                            else if (strategy === 'dipbuy') run_DipBuy(uniqueId);
                            else if (strategy === 'v38') run_V38(uniqueId);
                        }
                    } else {"""
    content = content.replace(select_tab_run_target, select_tab_run_replace)
    print("  [成功] 更新 selectStockTab")

    # ── 5. cleanCode 與名稱對照更新 ──
    get_stock_name_target = """        function getStockName(code) {
            const names = {
                s2330: '台積電', s2360: '致茂', s6205: '詮欣', s6669: '緯穎',
                s3443: '創意', s3189: '景碩', s3455: '由田', s3535: '晶彩科',
                s4908: '前鼎', s6269: '台郡', s6274: '台耀', s6261: '久元'
            };
            if (names[code]) return names[code];"""
    get_stock_name_replace = """        function getStockName(code) {
            const stock = preloadedStocks.find(s => s.id === code);
            if (stock) return stock.name;"""
    content = content.replace(get_stock_name_target, get_stock_name_replace)

    get_strat_display_target = """        function getStrategyDisplayName(code) {
            if (code === 's2330' || code === 's2360' || code === 's6205' || code === 's6274') return 'V4 均線修正';"""
    get_strat_display_replace = """        function getStrategyDisplayName(code) {
            const stock = preloadedStocks.find(s => s.id === code);
            if (stock) {
                if (stock.strategy === 'v4') return 'V4 均線修正';
                if (stock.strategy === 'rebound') return 'V_Rebound 反轉低接';
                if (stock.strategy === 'dipbuy') return 'V_Dip_Buy 動能低接';
                if (stock.strategy === 'v38') return 'V38 鎖利穩定版';
                if (stock.strategy === 'ai_trend') return 'AI 趨勢順勢策略';
                if (stock.strategy === 'ai_rebound') return 'AI 超跌反彈策略';
                if (stock.strategy === 'ai_oversold') return 'AI 極值超跌策略';
                if (stock.strategy === 'ai_support') return 'AI 支撐反彈策略';
            }"""
    content = content.replace(get_strat_display_target, get_strat_display_replace)

    clean_code_ui_target = "const cleanCode = pre.startsWith('custom_') ? pre.split('_')[2] : pre.substring(1);"
    clean_code_ui_replace = "const cleanCode = pre.startsWith('custom_') ? pre.split('_')[2] : pre.substring(1).split('_')[0];"
    content = content.replace(clean_code_ui_target, clean_code_ui_replace)

    clean_code_ui_target_2 = "code: pre.startsWith('custom_') ? pre.split('_')[2] : pre.substring(1),"
    clean_code_ui_replace_2 = "code: pre.startsWith('custom_') ? pre.split('_')[2] : pre.substring(1).split('_')[0],"
    content = content.replace(clean_code_ui_target_2, clean_code_ui_replace_2)
    print("  [成功] 更新 cleanCode 提取邏輯")

    # ── 6. parseData 技術指標延伸讀取 ──
    parse_data_target = """        const parseData = (rows) => {
            const p = (v) => v ? parseFloat(String(v).replace(/[↑↓,%\s]/g, '')) || 0 : 0;
            return rows.filter(r => r[0] && (String(r[0]).includes('/') || String(r[0]).includes('-') || /^\d{8}$/.test(r[0]))).map(r => ({
                date: String(r[0]).trim(), open: p(r[1]), high: p(r[2]), low: p(r[3]), close: p(r[4]),
                ma5: p(r[6]), ma20: p(r[7]), ma60: p(r[8]), ma120: p(r[9]), eom: p(r[10]), eomSig: p(r[11]), mfi: p(r[12]), macd: p(r[14])
            }));
        };"""
    parse_data_replace = """        const parseData = (rows) => {
            const p = (v) => v ? parseFloat(String(v).replace(/[↑↓,%\s]/g, '')) || 0 : 0;
            return rows.filter(r => r[0] && (String(r[0]).includes('/') || String(r[0]).includes('-') || /^\d{8}$/.test(r[0]))).map(r => ({
                date: String(r[0]).trim(), open: p(r[1]), high: p(r[2]), low: p(r[3]), close: p(r[4]),
                ma5: p(r[6]), ma20: p(r[7]), ma60: p(r[8]), ma120: p(r[9]), eom: p(r[10]), eomSig: p(r[11]), mfi: p(r[12]), macd: p(r[14]),
                k: p(r[15]), d: p(r[16]), rsi: p(r[17]), bias20: p(r[21]), cci: p(r[22]),
                bb_upper: p(r[24]), bb_lower: p(r[26]), pivot: p(r[28]), r1: p(r[29]), s1: p(r[30])
            }));
        };"""
    content = content.replace(parse_data_target, parse_data_replace)
    print("  [成功] 更新 parseData 函數支援多技術指標")

    # ── 7. createCustomStockPage 支援 ai 分類策略 ──
    create_page_v38_end = """                    <div class="param-group"><label>必須突破前高</label><select id="${uniqueId}_break_filter" onchange="run_V38('${uniqueId}')"><option value="yes" selected>是</option><option value="no">否</option></select></div>
                `;
            }"""

    create_page_ai_append = """\n            } else if (strategy.startsWith('ai_')) {
                const stock = preloadedStocks.find(s => s.id === uniqueId);
                const defaultEntry = stock ? stock.entry : '強勢均線多頭+KD金叉';
                const defaultExit = stock ? stock.exit : '6%停利 / 6%停損 (穩健勝率)';
                const defaultTp = stock ? stock.tp : 6.0;
                const defaultSl = stock ? stock.sl : 6.0;
                
                const entryOptions = [
                    "強勢均線多頭+KD金叉",
                    "中長期多頭+RSI低檔轉強",
                    "雙重均線突破+MACD翻紅",
                    "EOM動能突破+均線多頭",
                    "極度超跌共振 (BIAS+RSI+MFI)",
                    "布林通道下軌+KD低檔金叉",
                    "CCI超賣+MFI超賣+KD金叉",
                    "雙重超賣 (RSI+CCI)+MACD轉強",
                    "樞軸點(S1)支撐+KD金叉",
                    "突破阻力(R1)+MACD多頭",
                    "突破樞軸(Pivot)+RSI轉強",
                    "S1支撐不破+MACD紅柱增長",
                    "多頭拉回：MA60之上+KD金叉+RSI<45",
                    "布林中軌支撐+MACD紅柱",
                    "動能共振：EOM突破+MACD>0+RSI>50",
                    "雙保險超跌：BIAS超賣+布林下軌觸及",
                    "主力資金流入：MFI超賣+EOM突破",
                    "壓力突破：價格>R1+EOM強勢+MACD>0",
                    "長期均線支撐：站上MA120+KD金叉+CCI超賣",
                    "CCI超賣反彈+MACD紅柱增長"
                ].map(opt => `<option value="${opt}" ${opt === defaultEntry ? 'selected' : ''}>${opt}</option>`).join('');

                const exitOptions = [
                    "6%停利 / 6%停損 (穩健勝率)",
                    "8%停利 / 8%停損 (均衡配置)",
                    "12%停利 / 6%停損 (高盈虧比)",
                    "KD死叉離場或6%停損",
                    "RSI超買離場或6%停損",
                    "MACD紅柱縮短離場或6%停損",
                    "收盤跌破MA20或6%停損",
                    "觸碰布林上軌停利或6%停損",
                    "跌破樞軸支撐(S1)或8%停利"
                ].map(opt => `<option value="${opt}" ${opt === defaultExit ? 'selected' : ''}>${opt}</option>`).join('');

                controlPanelHtml = `
                    <div class="section-title">資金與基礎出口</div>
                    <div class="param-group"><label>交易張數</label><input type="number" id="${uniqueId}_sh" value="1" oninput="run_AI('${uniqueId}')"></div>
                    <div class="param-group"><label>固定停利 (%)</label><input type="number" id="${uniqueId}_tp" value="${defaultTp}" step="0.1" oninput="run_AI('${uniqueId}')"></div>
                    <div class="param-group"><label>固定停損 (%)</label><input type="number" id="${uniqueId}_sl" value="${defaultSl}" step="0.1" oninput="run_AI('${uniqueId}')"></div>
                    <div class="section-title">AI 交叉組合設定</div>
                    <div class="param-group" style="grid-column: span 2;"><label>AI 進場交叉組合</label>
                        <select id="${uniqueId}_entry_strat" onchange="run_AI('${uniqueId}')">
                            ${entryOptions}
                        </select>
                    </div>
                    <div class="param-group" style="grid-column: span 2;"><label>AI 出場交叉條件</label>
                        <select id="${uniqueId}_exit_strat" onchange="run_AI('${uniqueId}')">
                            ${exitOptions}
                        </select>
                    </div>
                `;
            }"""

    if create_page_v38_end in content:
        content = content.replace(create_page_v38_end, create_page_v38_end + create_page_ai_append)
        print("  [成功] 更新 createCustomStockPage 支援 ai 分類")

    # ── 8. 注入 run_AI 核心回測引擎 ──
    run_ai_js = """
        // --- V5 新增: AI 交叉指標組合回測引擎 ---
        function run_AI(uniqueId) {
            console.log("[DEBUG] run_AI called with uniqueId:", uniqueId);
            const ds = dataStore[uniqueId]; if(!ds) return;
            
            // 取得參數
            const sh = parseInt(document.getElementById(uniqueId + '_sh').value) * 1000;
            const tpVal = parseFloat(document.getElementById(uniqueId + '_tp').value);
            const slVal = parseFloat(document.getElementById(uniqueId + '_sl').value);
            
            const tp = tpVal > 0 ? tpVal / 100 : null;
            const sl = slVal > 0 ? slVal / 100 : null;
            
            const entryStrat = document.getElementById(uniqueId + '_entry_strat').value;
            const exitStrat = document.getElementById(uniqueId + '_exit_strat').value;
            
            // 預計算所有訊號陣列，加速回測
            const entrySignals = new Array(ds.length).fill(false);
            const exitSignals = new Array(ds.length).fill(false);
            
            for (let i = 1; i < ds.length; i++) {
                const c = ds[i];
                const prev = ds[i-1];
                
                // 16種進場訊號計算
                let f_kd_gold = (c.k > c.d) && (prev.k <= prev.d);
                let f_rsi_oversold = c.rsi < 35;
                let f_rsi_bull = c.rsi > 50;
                let f_macd_grow = c.macd > prev.macd;
                let f_macd_positive = c.macd > 0;
                let f_bias_oversold = c.bias20 < -4;
                let f_cci_oversold = c.cci < -100;
                let f_eom_bullish = c.eom > c.eomSig;
                let f_mfi_oversold = c.mfi < 30;
                let f_bb_oversold = (c.close < c.bb_lower) && (c.bb_lower > 0);
                let f_above_pivot = c.close > c.pivot;
                let f_break_r1 = (c.close > c.r1) && (c.r1 > 0);
                let f_ma_bull = (c.ma5 > c.ma20) && (c.ma20 > c.ma60);
                let f_above_ma20 = c.close > c.ma20;
                let f_above_ma60 = c.close > c.ma60;
                let f_above_ma120 = c.close > c.ma120;
                
                // 進場訊號判定
                let condLong = false;
                if (entryStrat === "強勢均線多頭+KD金叉") condLong = f_ma_bull && f_kd_gold && f_above_ma20;
                else if (entryStrat === "中長期多頭+RSI低檔轉強") condLong = f_above_ma60 && f_above_ma120 && (c.rsi < 45) && f_macd_grow;
                else if (entryStrat === "雙重均線突破+MACD翻紅") condLong = f_above_ma20 && f_above_ma60 && f_macd_positive && f_macd_grow;
                else if (entryStrat === "EOM動能突破+均線多頭") condLong = f_eom_bullish && f_ma_bull && f_above_ma20;
                else if (entryStrat === "極度超跌共振 (BIAS+RSI+MFI)") condLong = f_bias_oversold && f_rsi_oversold && f_mfi_oversold;
                else if (entryStrat === "布林通道下軌+KD低檔金叉") condLong = f_bb_oversold && f_kd_gold;
                else if (entryStrat === "CCI超賣+MFI超賣+KD金叉") condLong = f_cci_oversold && f_mfi_oversold && f_kd_gold;
                else if (entryStrat === "雙重超賣 (RSI+CCI)+MACD轉強") condLong = f_rsi_oversold && f_cci_oversold && f_macd_grow;
                else if (entryStrat === "樞軸點(S1)支撐+KD金叉") condLong = (c.close > c.s1) && (c.low <= c.s1) && f_kd_gold && (c.s1 > 0);
                else if (entryStrat === "突破阻力(R1)+MACD多頭") condLong = f_break_r1 && f_macd_positive && f_above_ma20;
                else if (entryStrat === "突破樞軸(Pivot)+RSI轉強") condLong = f_above_pivot && f_rsi_bull && f_macd_grow;
                else if (entryStrat === "S1支撐不破+MACD紅柱增長") condLong = (c.close > c.s1) && f_macd_grow && (c.s1 > 0);
                else if (entryStrat === "多頭拉回：MA60之上+KD金叉+RSI<45") condLong = f_above_ma60 && f_kd_gold && (c.rsi < 45);
                else if (entryStrat === "布林中軌支撐+MACD紅柱") condLong = (c.close > c.bb_lower) && (c.close < c.bb_upper) && f_above_ma20 && f_macd_grow;
                else if (entryStrat === "動能共振：EOM突破+MACD>0+RSI>50") condLong = f_eom_bullish && f_macd_positive && f_rsi_bull;
                else if (entryStrat === "雙保險超跌：BIAS超賣+布林下軌觸及") condLong = f_bias_oversold && f_bb_oversold;
                else if (entryStrat === "主力資金流入：MFI超賣+EOM突破") condLong = f_mfi_oversold && f_eom_bullish;
                else if (entryStrat === "壓力突破：價格>R1+EOM強勢+MACD>0") condLong = f_break_r1 && f_eom_bullish && f_macd_positive;
                else if (entryStrat === "長期均線支撐：站上MA120+KD金叉+CCI超賣") condLong = f_above_ma120 && f_kd_gold && f_cci_oversold;
                else if (entryStrat === "CCI超賣反彈+MACD紅柱增長") condLong = f_cci_oversold && f_macd_grow && f_above_ma20;
                
                entrySignals[i] = condLong;
                
                // 9種出場訊號計算
                let f_kd_dead = (c.k < c.d) && (prev.k >= prev.d);
                let f_rsi_overbought = c.rsi > 65;
                let f_macd_shrink = c.macd < prev.macd;
                let f_below_ma20 = c.close < c.ma20;
                let f_bb_overbought = (c.close > c.bb_upper) && (c.bb_upper > 0);
                let f_below_s1 = (c.close < c.s1) && (c.s1 > 0);
                
                let condExit = false;
                if (exitStrat === "KD死叉離場或6%停損") condExit = f_kd_dead;
                else if (exitStrat === "RSI超買離場或6%停損") condExit = f_rsi_overbought;
                else if (exitStrat === "MACD紅柱縮短離場或6%停損") condExit = f_macd_shrink;
                else if (exitStrat === "收盤跌破MA20或6%停損") condExit = f_below_ma20;
                else if (exitStrat === "觸碰布林上軌停利或6%停損") condExit = f_bb_overbought;
                else if (exitStrat === "跌破樞軸支撐(S1)或8%停利") condExit = f_below_s1;
                
                exitSignals[i] = condExit;
            }
            
            // 執行交易迴圈 (次日開盤交易基準，完全對齊 Python)
            let trd = [], hold = false, bp = 0, tot = 0, mCap = 0;
            let bi = new Array(ds.length).fill(null), si = new Array(ds.length).fill(null);
            for (let i = 1; i < ds.length - 1; i++) {
                const c = ds[i];
                const n = ds[i+1];
                
                if (!hold) {
                    if (entrySignals[i]) {
                        hold = true;
                        bp = n.open;
                        bi[i+1] = 1;
                        mCap = Math.max(mCap, bp * sh);
                        trd.push({ type: '買入', date: n.date, price: bp, info: 'AI 進場訊號觸發' });
                    }
                } else {
                    const pnlR = (n.open - bp) / bp;
                    
                    // 停利停損檢查
                    const cond_tp = (tp !== null) && (pnlR >= tp);
                    const cond_sl = (sl !== null) && (pnlR <= -sl);
                    const cond_sig = exitSignals[i];
                    
                    if (cond_tp || cond_sl || cond_sig) {
                        hold = false;
                        const ep = n.open;
                        const p = (ep - bp) * sh;
                        tot += p;
                        si[i+1] = 1;
                        
                        let infoStr = 'AI 出場條件觸發';
                        if (cond_tp) infoStr = 'AI 停利出口';
                        else if (cond_sl) infoStr = 'AI 停損出口';
                        
                        trd.push({ type: '賣出', date: n.date, price: ep, info: infoStr, pnl: p, entP: bp });
                    }
                }
            }
            
            updateUI(uniqueId, trd, tot, mCap, ds, bi, si);
        }
        
"""
    update_ui_func_target = "        function updateUI(pre, trd, tot, mCap, ds, bi, si) {"
    if update_ui_func_target in content:
        content = content.replace(update_ui_func_target, run_ai_js + update_ui_func_target)
        print("  [成功] 注入 run_AI 核心回測引擎")

    # 儲存修改後的 HTML 檔案
    with open(HTML_OUT_PATH, 'w', encoding='utf-8') as f:
        f.write(content)
    print("  [成功] 儲存至 dashboard_v6.html")

    # ── 9. 修改 server.js 預設重導向 ──
    with open(SERVER_PATH, 'r', encoding='utf-8') as f:
        server_code = f.read()

    old_redirect = """// 預設頁面重導向至 index_v2.html (登入頁)
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index_v2.html'));
});"""

    new_redirect = """// 預設頁面重導向至 index_v3.html (新版含排行榜登入頁)
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index_v3.html'));
});"""

    if old_redirect in server_code:
        server_code = server_code.replace(old_redirect, new_redirect)
        print("  [成功] 修改 server.js 預設頁面重導向為 index_v3.html")
    else:
        # 嘗試只替換檔名
        fallback_redirect = "index_v2.html"
        if fallback_redirect in server_code:
            server_code = server_code.replace(fallback_redirect, "index_v3.html")
            print("  [成功] 修改 server.js 預設頁面重導向為 index_v3.html (降級模式)")
        else:
            print("  [警告] 找不到 server.js 預設頁面重導向配置")

    with open(SERVER_PATH, 'w', encoding='utf-8') as f:
        f.write(server_code)

    print("=" * 60)
    print("  補丁套用完畢，新網頁已更新並成功分類！")
    print("=" * 60)

if __name__ == "__main__":
    main()
