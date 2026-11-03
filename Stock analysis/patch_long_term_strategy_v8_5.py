# -*- coding: utf-8 -*-
"""
================================================================================
長期佈局策略升級補丁 (patch_long_term_strategy_v8_5.py)
1. 增加檢視期別切換按鈕組 (2026-10 最新 / 2026-07 歷史 / 兩期差異對照)
2. 候選清單表格新增「異動趨勢」欄位與狀態標籤 (🔥 新進榜、📈 增持、📉 減持、持平)
3. 基金與 ETF 柱狀圖 Tooltip 標題改為顯示代號 (例如: ACOB61, 0050)
================================================================================
"""

import os
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')
except Exception:
    pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER_PUBLIC_DIR = os.path.join(SCRIPT_DIR, "修正版_V6_Server", "public")
TARGET_FILE = os.path.join(SERVER_PUBLIC_DIR, "dashboard_v8_4_backup.html")

def apply_patch():
    print(f"正在更新長期佈局策略至: {TARGET_FILE} ...")
    with open(TARGET_FILE, 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. 調整 HTML 控制項區塊，加入期別切換按鈕組
    old_ctrl_section = """                <div style="display: flex; flex-wrap: wrap; gap: 15px; margin-bottom: 20px;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span>顯示前 N 名：</span>"""

    new_ctrl_section = """                <div style="display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 15px; margin-bottom: 20px;">
                    <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
                        <span>顯示前 N 名：</span>"""

    if old_ctrl_section in html:
        html = html.replace(old_ctrl_section, new_ctrl_section)
        print("✅ 1a. 控制項容器寬度樣式更新完成")
    else:
        print("⚠️ 1a. 未找到 old_ctrl_section，可能已套用")

    old_scale_end = """                        <select id="filter_fund_scale" onchange="renderLongTermCandidates()"
                            style="padding: 6px 12px; border-radius: 6px; border: 1px solid #cbd5e1; font-weight: bold; cursor: pointer;">
                            <option value="0">全部 (不限規模)</option>
                            <option value="50">50 億元以上</option>
                            <option value="100">100 億元以上</option>
                            <option value="200">200 億元以上</option>
                            <option value="500">500 億元以上</option>
                            <option value="1000">1000 億元以上</option>
                        </select>
                    </div>
                </div>"""

    new_scale_end = """                        <select id="filter_fund_scale" onchange="renderLongTermCandidates()"
                            style="padding: 6px 12px; border-radius: 6px; border: 1px solid #cbd5e1; font-weight: bold; cursor: pointer;">
                            <option value="0">全部 (不限規模)</option>
                            <option value="50">50 億元以上</option>
                            <option value="100">100 億元以上</option>
                            <option value="200">200 億元以上</option>
                            <option value="500">500 億元以上</option>
                            <option value="1000">1000 億元以上</option>
                        </select>
                    </div>

                    <!-- 💎 月份切換與異動模式按鈕組 -->
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="font-weight: 700; font-size: 0.9rem; color: #475569;">檢視期別：</span>
                        <div id="long_term_month_toggle_group" style="display: inline-flex; background: rgba(0,0,0,0.06); padding: 3px; border-radius: 8px; gap: 4px;">
                            <button id="btn_month_curr" onclick="switchLongTermMonth('curr')"
                                style="padding: 6px 14px; border: none; border-radius: 6px; font-weight: 700; font-size: 0.85rem; cursor: pointer; transition: all 0.2s; background: #6366f1; color: white; box-shadow: 0 2px 4px rgba(99, 102, 241, 0.3);">
                                🔥 2026-10 (最新)
                            </button>
                            <button id="btn_month_base" onclick="switchLongTermMonth('base')"
                                style="padding: 6px 14px; border: none; border-radius: 6px; font-weight: 700; font-size: 0.85rem; cursor: pointer; transition: all 0.2s; background: transparent; color: #64748b;">
                                📅 2026-07 (前期)
                            </button>
                            <button id="btn_month_diff" onclick="switchLongTermMonth('diff')"
                                style="padding: 6px 14px; border: none; border-radius: 6px; font-weight: 700; font-size: 0.85rem; cursor: pointer; transition: all 0.2s; background: transparent; color: #64748b;">
                                📊 兩期差異對照
                            </button>
                        </div>
                    </div>
                </div>"""

    if old_scale_end in html:
        html = html.replace(old_scale_end, new_scale_end)
        print("✅ 1b. 注入期別切換按鈕組完成")
    else:
        print("⚠️ 1b. 未找到 old_scale_end，可能已套用")

    # 2. 候選清單表格加入「異動趨勢」欄位
    old_table_header = """                                    <th style="padding:10px; font-weight:700;">排名</th>
                                    <th style="padding:10px; font-weight:700;">個股名稱</th>
                                    <th style="padding:10px; font-weight:700; color:#a855f7;">共同基金數</th>"""

    new_table_header = """                                    <th style="padding:10px; font-weight:700;">排名</th>
                                    <th style="padding:10px; font-weight:700;">個股名稱</th>
                                    <th id="th_long_term_trend" style="padding:10px; font-weight:700; color:#f59e0b;">異動趨勢 (vs 07月)</th>
                                    <th style="padding:10px; font-weight:700; color:#a855f7;">共同基金數</th>"""

    if old_table_header in html:
        html = html.replace(old_table_header, new_table_header)
        print("✅ 2. 表格標題加入「異動趨勢 (vs 07月)」欄位完成")
    else:
        print("⚠️ 2. 未找到 old_table_header，可能已套用")

    # 3. 調整長條圖 Tooltip 標題顯示基金代號
    old_render_chart_tooltip = """                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                callbacks: {
                                    label: function (context) {"""

    new_render_chart_tooltip = """                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                callbacks: {
                                    title: function (context) {
                                        const fund = dataList[context[0].dataIndex];
                                        return (fund && fund.code) ? fund.code : context[0].label;
                                    },
                                    label: function (context) {"""

    if old_render_chart_tooltip in html:
        html = html.replace(old_render_chart_tooltip, new_render_chart_tooltip)
        print("✅ 3a. 共同基金與 ETF 柱狀圖 Tooltip 標題改為代號完成")
    else:
        print("⚠️ 3a. 未找到 old_render_chart_tooltip，可能已套用")

    old_company_chart_tooltip = """                    plugins: {
                        legend: { labels: { color: textColor } },
                        tooltip: { mode: 'index', intersect: false }
                    },"""

    new_company_chart_tooltip = """                    plugins: {
                        legend: { labels: { color: textColor } },
                        tooltip: {
                            mode: 'index',
                            intersect: false,
                            callbacks: {
                                title: function (context) {
                                    const fund = funds[context[0].dataIndex];
                                    return (fund && fund.code) ? fund.code : context[0].label;
                                }
                            }
                        }
                    },"""

    if old_company_chart_tooltip in html:
        html = html.replace(old_company_chart_tooltip, new_company_chart_tooltip)
        print("✅ 3b. 投信公司圖表 Tooltip 標題改為代號完成")
    else:
        print("⚠️ 3b. 未找到 old_company_chart_tooltip，可能已套用")

    # 4. 替換/升級 JavaScript 邏輯 (包含 switchLongTermMonth 與 renderLongTermCandidates)
    old_js_block_start = """        async function loadLongTermData() {"""
    old_js_block_end = """        function showHoldingFundsDetail(stockName) {"""

    new_js_block = """        let globalRawLongTermPayload = null;
        let currentLongTermMonthMode = 'curr'; // 'curr' | 'base' | 'diff'

        function switchLongTermMonth(mode) {
            currentLongTermMonthMode = mode;
            const btnCurr = document.getElementById('btn_month_curr');
            const btnBase = document.getElementById('btn_month_base');
            const btnDiff = document.getElementById('btn_month_diff');
            const thTrend = document.getElementById('th_long_term_trend');

            const activeStyle = "padding: 6px 14px; border: none; border-radius: 6px; font-weight: 700; font-size: 0.85rem; cursor: pointer; transition: all 0.2s; background: #6366f1; color: white; box-shadow: 0 2px 4px rgba(99, 102, 241, 0.3);";
            const inactiveStyle = "padding: 6px 14px; border: none; border-radius: 6px; font-weight: 700; font-size: 0.85rem; cursor: pointer; transition: all 0.2s; background: transparent; color: #64748b;";

            if (btnCurr) btnCurr.style.cssText = (mode === 'curr') ? activeStyle : inactiveStyle;
            if (btnBase) btnBase.style.cssText = (mode === 'base') ? activeStyle : inactiveStyle;
            if (btnDiff) btnDiff.style.cssText = (mode === 'diff') ? activeStyle : inactiveStyle;

            if (thTrend) {
                thTrend.innerText = (mode === 'base') ? '期別標記' : '異動趨勢 (vs 07月)';
            }

            renderLongTermCandidates();
        }

        async function loadLongTermData() {
            const tableBody = document.getElementById('long_term_candidates_body');
            const fundsListContainer = document.getElementById('long_term_funds_list_container');
            const dateLabel = document.getElementById('long_term_data_date');

            if (tableBody) tableBody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:30px; color:#94a3b8;">⏳ 正在向伺服器請求最新持股分析資料...</td></tr>`;
            if (fundsListContainer) fundsListContainer.innerHTML = `<div style="text-align:center; color:#94a3b8; padding: 20px;">⏳ 正在加載...</div>`;

            try {
                // 1. 取得候選股票
                const resCandidates = await fetch('/api/fund_candidates');
                if (!resCandidates.ok) throw new Error(await resCandidates.text());
                const rawCandidates = await resCandidates.json();

                globalRawLongTermPayload = rawCandidates;
                let candidates = [];
                if (rawCandidates && rawCandidates.date) {
                    const baseDateStr = rawCandidates.base_date ? ` (前期基期: ${rawCandidates.base_date})` : '';
                    if (dateLabel) dateLabel.innerText = `📅 最新資料: ${rawCandidates.date}${baseDateStr}`;
                    candidates = rawCandidates.candidates || [];
                } else {
                    candidates = rawCandidates || []; // 相容舊版
                }

                globalLongTermCandidates = candidates;

                // 2. 取得前10大基金清單
                const resFunds = await fetch('/api/top10_funds');
                if (!resFunds.ok) throw new Error(await resFunds.text());
                globalTop10Funds = await resFunds.json();

                // 3. 取得官方 ETF 字典
                try {
                    const resETF = await fetch('/api/etf_list');
                    if (resETF.ok) {
                        globalETFList = await resETF.json();
                    }
                } catch (e) {
                    console.warn("無法取得官方 ETF 字典，將使用預設關鍵字篩選", e);
                }

                // 渲染投信公司列表
                if (fundsListContainer) {
                    fundsListContainer.innerHTML = '';
                    const isDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
                    const selectBg = isDark ? 'rgba(15, 23, 42, 0.8)' : '#ffffff';
                    const selectBorder = isDark ? 'rgba(255,255,255,0.2)' : '#e2e8f0';
                    const selectColor = isDark ? '#f8fafc' : '#1e293b';
                    let html = `<select onchange="if(this.value) showCompanyFundsChart(this.value)" style="width: 100%; padding: 12px 15px; background: ${selectBg}; border: 1px solid ${selectBorder}; border-radius: 8px; color: ${selectColor}; font-weight: bold; cursor: pointer; font-size: 1rem; outline: none; appearance: none; background-image: url('data:image/svg+xml;utf8,<svg fill=%22%2394a3b8%22 height=%2224%22 viewBox=%220 0 24 24%22 width=%2224%22 xmlns=%22http://www.w3.org/2000/svg%22><path d=%22M7 10l5 5 5-5z%22/></svg>'); background-repeat: no-repeat; background-position: right 10px center;">`;
                    html += `<option value="">🔽 請選擇投信公司</option>`;
                    for (const comp of Object.keys(globalTop10Funds)) {
                        html += `<option value="${comp}">🏢 ${comp}</option>`;
                    }
                    html += '</select>';
                    fundsListContainer.innerHTML = html;

                    // 自動選擇並顯示綜合評比
                    const selectEl = fundsListContainer.querySelector('select');
                    if (selectEl && globalTop10Funds['綜合評比']) {
                        selectEl.value = '綜合評比';
                        showCompanyFundsChart('綜合評比');
                    }
                }

                // 渲染候選清單 (依據目前 Top N 選項與期別)
                renderLongTermCandidates();

            } catch (err) {
                console.error("載入長期佈局資料失敗:", err);
                let errObj;
                try { errObj = JSON.parse(err.message); } catch (e) { errObj = { error: err.message }; }
                if (tableBody) tableBody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:30px; color:#ef4444;">❌ 無法載入資料: ${errObj.error}</td></tr>`;
                if (fundsListContainer) fundsListContainer.innerHTML = `<div style="text-align:center; color:#ef4444; padding: 20px;">❌ 載入失敗</div>`;
            }
        }

        function getFundScale(code) {
            if (globalETFList && globalETFList.items) {
                const etf = globalETFList.items.find(e => e.code === code);
                if (etf && etf.scale) return etf.scale;
            }
            if (globalTop10Funds) {
                for (const comp in globalTop10Funds) {
                    const fund = globalTop10Funds[comp].find(f => f.code === code);
                    if (fund && fund.scale) return fund.scale;
                }
            }
            return 0;
        }

        function renderLongTermCandidates() {
            const tableBody = document.getElementById('long_term_candidates_body');
            if (!tableBody) return;

            const topN = parseInt(document.getElementById('long_term_top_n').value || 50);
            const scaleFilterEle = document.getElementById('filter_fund_scale');
            const scaleThreshold = scaleFilterEle ? parseFloat(scaleFilterEle.value) : 0;
            
            // 決定顯示清單來源
            let sourceList = [];
            if (currentLongTermMonthMode === 'base') {
                sourceList = (globalRawLongTermPayload && globalRawLongTermPayload.candidates_base) ? globalRawLongTermPayload.candidates_base : [];
            } else if (currentLongTermMonthMode === 'diff') {
                sourceList = (globalLongTermCandidates || []).filter(item => item.status === 'new' || item.status === 'increase' || item.status === 'decrease');
                // 依新進榜優先、其次依增減幅度降冪
                sourceList.sort((a, b) => {
                    if (a.status === 'new' && b.status !== 'new') return -1;
                    if (a.status !== 'new' && b.status === 'new') return 1;
                    return (b.diff_count - a.diff_count) || (b.diff_qty - a.diff_qty);
                });
            } else {
                sourceList = globalLongTermCandidates || [];
            }

            // 依基金規模進行篩選
            let filteredCandidates = [];
            sourceList.forEach(item => {
                if (!item.funds) return;
                
                let validFunds = item.funds.filter(fObj => {
                    const scale = getFundScale(fObj.code);
                    return scale >= scaleThreshold;
                });
                
                if (validFunds.length > 0) {
                    filteredCandidates.push({
                        ...item,
                        funds: validFunds,
                        total_valid: validFunds.length
                    });
                }
            });

            if (currentLongTermMonthMode !== 'diff') {
                filteredCandidates.sort((a, b) => b.total_valid - a.total_valid);
            }
            
            const displayList = filteredCandidates.slice(0, topN);

            if (displayList.length === 0) {
                tableBody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:30px; color:#94a3b8;">📭 目前沒有符合篩選條件的個股</td></tr>`;
                return;
            }

            tableBody.innerHTML = '';

            displayList.forEach((item, index) => {
                let mfCount = 0;
                let etfCount = 0;
                let mfQty = 0;
                let etfQty = 0;

                if (item.funds) {
                    item.funds.forEach(fObj => {
                        let fName = "";
                        for (let comp in globalTop10Funds) {
                            let match = globalTop10Funds[comp].find(x => x.code === fObj.code);
                            if (match) { fName = match.name; break; }
                        }

                        let qty = parseFloat(String(fObj.qty).replace(/,/g, '')) || 0;
                        if (fName && isFundETF(fObj.code, fName)) {
                            etfCount++;
                            etfQty += qty;
                        } else {
                            mfCount++;
                            mfQty += qty;
                        }
                    });
                }

                // 異動徽章生成
                let trendHtml = '<span style="color:#94a3b8; font-size:0.8rem;">-</span>';
                if (currentLongTermMonthMode === 'base') {
                    trendHtml = '<span style="color:#64748b; font-size:0.8rem;">📅 2026-07 基期</span>';
                } else if (item.status === 'new') {
                    trendHtml = `<span style="background: rgba(239, 68, 68, 0.15); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.3); padding: 3px 8px; border-radius: 6px; font-weight: 700; font-size: 0.8rem;">🔥 新進榜</span>`;
                } else if (item.status === 'increase') {
                    const countTxt = item.diff_count > 0 ? `+${item.diff_count}檔` : '';
                    const qtyTxt = item.diff_qty > 0 ? ` (+${item.diff_qty >= 1000 ? (item.diff_qty/1000).toFixed(0)+'張' : item.diff_qty+'股'})` : '';
                    trendHtml = `<span style="background: rgba(16, 185, 129, 0.15); color: #059669; border: 1px solid rgba(16, 185, 129, 0.3); padding: 3px 8px; border-radius: 6px; font-weight: 700; font-size: 0.8rem;">📈 增持 ${countTxt}${qtyTxt}</span>`;
                } else if (item.status === 'decrease') {
                    const countTxt = item.diff_count < 0 ? `${item.diff_count}檔` : '';
                    const qtyTxt = item.diff_qty < 0 ? ` (${item.diff_qty <= -1000 ? (item.diff_qty/1000).toFixed(0)+'張' : item.diff_qty+'股'})` : '';
                    trendHtml = `<span style="background: rgba(249, 115, 22, 0.15); color: #d97706; border: 1px solid rgba(249, 115, 22, 0.3); padding: 3px 8px; border-radius: 6px; font-weight: 700; font-size: 0.8rem;">📉 減持 ${countTxt}${qtyTxt}</span>`;
                } else if (item.status === 'flat') {
                    trendHtml = `<span style="background: rgba(100, 116, 139, 0.15); color: #64748b; border: 1px solid rgba(100, 116, 139, 0.3); padding: 3px 8px; border-radius: 6px; font-weight: 700; font-size: 0.8rem;">持平</span>`;
                }

                const tr = document.createElement('tr');
                tr.id = 'row_candidate_' + item.stock_name;
                tr.innerHTML = `
                    <td style="padding:10px; font-weight:700; font-size:0.9rem;">#${index + 1}</td>
                    <td style="padding:10px; font-weight:700; color:#818cf8; font-size:0.95rem;">${item.stock_name}</td>
                    <td style="padding:10px;">${trendHtml}</td>
                    <td style="padding:10px;">
                        <button onclick="showHoldingFundsDetail('${item.stock_name}')" style="background: rgba(168, 85, 247, 0.15); color: #a855f7; padding: 4px 10px; border-radius: 6px; font-weight: 700; font-size: 0.9rem; border: 1px solid rgba(168, 85, 247, 0.4); cursor: pointer; transition: all 0.2s;" onmouseover="this.style.background='rgba(168, 85, 247, 0.3)'" onmouseout="this.style.background='rgba(168, 85, 247, 0.15)'">
                            ${mfCount} 檔
                        </button>
                    </td>
                    <td style="padding:10px;">
                        <button onclick="showHoldingFundsDetail('${item.stock_name}')" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8; padding: 4px 10px; border-radius: 6px; font-weight: 700; font-size: 0.9rem; border: 1px solid rgba(56, 189, 248, 0.4); cursor: pointer; transition: all 0.2s;" onmouseover="this.style.background='rgba(56, 189, 248, 0.3)'" onmouseout="this.style.background='rgba(56, 189, 248, 0.15)'">
                            ${etfCount} 檔
                        </button>
                    </td>
                    <td style="padding:10px; font-weight:bold; color: #a855f7; font-size:0.9rem;">${mfQty.toLocaleString()}</td>
                    <td style="padding:10px; font-weight:bold; color: #38bdf8; font-size:0.9rem;">${etfQty.toLocaleString()}</td>
                    <td style="padding:10px;">
                        <button onclick="alert('基本面分析建置中，敬請期待 (目前標的: ${item.stock_name})')" style="padding: 4px 8px; font-size: 0.85rem; background: rgba(59, 130, 246, 0.2); border: 1px solid rgba(59, 130, 246, 0.4); color: #60a5fa; border-radius: 6px; cursor: pointer;">🔍 分析</button>
                    </td>
                `;
                tableBody.appendChild(tr);
            });
        }
"""

    start_idx = html.find(old_js_block_start)
    end_idx = html.find(old_js_block_end)

    if start_idx != -1 and end_idx != -1:
        html = html[:start_idx] + new_js_block + "\n        " + html[end_idx:]
        print("✅ 4. 替換 JavaScript 核心邏輯 (多期切換與渲染) 完成")
    else:
        print(f"⚠️ 4. 未找到 JS 區塊邊界 (start_idx={start_idx}, end_idx={end_idx})")

    with open(TARGET_FILE, 'w', encoding='utf-8') as f:
        f.write(html)
    print("🎉 成功將長期佈局策略升級寫入 dashboard_v8_4_backup.html！")

if __name__ == '__main__':
    apply_patch()
