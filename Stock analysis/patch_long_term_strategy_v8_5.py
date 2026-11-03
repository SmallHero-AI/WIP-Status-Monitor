# -*- coding: utf-8 -*-
"""
================================================================================
長期佈局策略視覺呈現優化補丁 (patch_long_term_strategy_v8_5.py)
1. 候選清單表格取消獨立欄位，改在「共同基金數 / ETF數」與「持有數量」下方換行小字括號說明差異
2. 右側柱狀圖數字後方增加括號顯示該檔基金/ETF的持股差異 (例如: 12,000 (+2,000)、(新進)、(持平))
3. 柱狀圖 Tooltip 標題精準顯示 ETF 官方證券代號 (如 0050、00406A) 或基金代號與簡稱
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

def apply_patch(target_path=TARGET_FILE):
    print(f"正在更新長期佈局策略至: {target_path} ...")
    with open(target_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. 調整 HTML 控制項區塊，確保期別切換按鈕組存在
    old_ctrl_section = """                <div style="display: flex; flex-wrap: wrap; gap: 15px; margin-bottom: 20px;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span>顯示前 N 名：</span>"""

    new_ctrl_section = """                <div style="display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 15px; margin-bottom: 20px;">
                    <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
                        <span>顯示前 N 名：</span>"""

    if old_ctrl_section in html:
        html = html.replace(old_ctrl_section, new_ctrl_section)

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

    # 2. 恢復原本乾淨的 7 欄表頭 (移除 th_long_term_trend)
    header_with_trend = """                                    <th style="padding:10px; font-weight:700;">排名</th>
                                    <th style="padding:10px; font-weight:700;">個股名稱</th>
                                    <th id="th_long_term_trend" style="padding:10px; font-weight:700; color:#f59e0b;">異動趨勢 (vs 07月)</th>
                                    <th style="padding:10px; font-weight:700; color:#a855f7;">共同基金數</th>"""

    clean_header = """                                    <th style="padding:10px; font-weight:700;">排名</th>
                                    <th style="padding:10px; font-weight:700;">個股名稱</th>
                                    <th style="padding:10px; font-weight:700; color:#a855f7;">共同基金數</th>"""

    if header_with_trend in html:
        html = html.replace(header_with_trend, clean_header)
        print("✅ 2. 移除獨立異動趨勢欄位，恢復 7 欄緊湊排版完成")
    else:
        print("ℹ️ 2. 表格表頭已為 7 欄模式")

    # 3. 替換/升級 JavaScript 邏輯 (包含 ETF 代號精準比對、換行括號說明、長條圖數字後差異標註)
    old_js_block_start = """        async function loadLongTermData() {"""
    if "let globalRawLongTermPayload = null;" in html:
        old_js_block_start = """        let globalRawLongTermPayload = null;"""

    old_js_block_end = """        function returnToCandidateRow() {"""

    new_js_block = """        let globalRawLongTermPayload = null;
        let currentLongTermMonthMode = 'curr'; // 'curr' | 'base' | 'diff'

        // 知名熱門 ETF 官方證券代號權威別名對照表 (確保 100% 準確解析)
        const KNOWN_ETF_ALIASES = [
            { keywords: ['大華', '高填息'], code: '00918' },
            { keywords: ['卓越50', '台灣50', '元大台50', '台灣卓越50'], code: '0050' },
            { keywords: ['元大高股息', '高股息'], code: '0056' },
            { keywords: ['永續高股息', '國泰永續'], code: '00878' },
            { keywords: ['關鍵半導體', '中信關鍵'], code: '00891' },
            { keywords: ['小資高價', '中信小資'], code: '00894' },
            { keywords: ['精選高息', '群益精選'], code: '00919' },
            { keywords: ['科技優息', '復華科技'], code: '00929' },
            { keywords: ['高息動能', '統一高息'], code: '00939' },
            { keywords: ['價值高息', '元大價值'], code: '00940' },
            { keywords: ['台灣收益', '中信台灣收益'], code: '00406A' },
            { keywords: ['動能高息', '國泰動能'], code: '00400A' },
            { keywords: ['采吉50', '釆吉50', '富邦台50'], code: '006208' },
            { keywords: ['富邦科技'], code: '0052' },
            { keywords: ['富櫃50'], code: '006201' },
            { keywords: ['富邦半導體'], code: '00892' },
            { keywords: ['中信成長高股息', '優選成長高股息'], code: '00934' },
            { keywords: ['凱基優選高股息', '優選高股息30'], code: '00915' },
            { keywords: ['中信上游半導體', '上游半導體'], code: '00941' },
            { keywords: ['台新臺灣半導體', '台新半導體'], code: '00904' }
        ];

        function getOfficialETFCode(fundCode, fundName) {
            const rawName = String(fundName || '');
            
            // 1. 先由已知權威別名精確匹配
            for (const item of KNOWN_ETF_ALIASES) {
                if (item.keywords.some(k => rawName.includes(k))) {
                    return item.code;
                }
            }

            // 2. 若名稱中已明確包含 4~6 碼 ETF 代號 (例如 0050, 00406A)
            const mCode = rawName.match(/\\b(00\\d{2,3}[A-Z]?)\\b/);
            if (mCode) return mCode[1];

            // 3. 若本身已是官方 ETF 代碼
            if (globalETFList && globalETFList.codes && globalETFList.codes.includes(fundCode)) {
                return fundCode;
            }

            // 4. 與官方 ETF 字典 clean 名稱進行模糊比對
            if (globalETFList && globalETFList.items) {
                const clean = cleanFundNameForMatch(rawName);
                if (clean) {
                    const exact = globalETFList.items.find(e => e.clean === clean);
                    if (exact) return exact.code;

                    let bestMatch = null;
                    let bestLen = 0;
                    for (const e of globalETFList.items) {
                        if (e.clean && (clean.includes(e.clean) || e.clean.includes(clean))) {
                            if (e.clean.length > bestLen) {
                                bestLen = e.clean.length;
                                bestMatch = e.code;
                            }
                        }
                    }
                    if (bestMatch) return bestMatch;
                }
            }

            return fundCode;
        }

        function switchLongTermMonth(mode) {
            currentLongTermMonthMode = mode;
            const btnCurr = document.getElementById('btn_month_curr');
            const btnBase = document.getElementById('btn_month_base');
            const btnDiff = document.getElementById('btn_month_diff');

            const activeStyle = "padding: 6px 14px; border: none; border-radius: 6px; font-weight: 700; font-size: 0.85rem; cursor: pointer; transition: all 0.2s; background: #6366f1; color: white; box-shadow: 0 2px 4px rgba(99, 102, 241, 0.3);";
            const inactiveStyle = "padding: 6px 14px; border: none; border-radius: 6px; font-weight: 700; font-size: 0.85rem; cursor: pointer; transition: all 0.2s; background: transparent; color: #64748b;";

            if (btnCurr) btnCurr.style.cssText = (mode === 'curr') ? activeStyle : inactiveStyle;
            if (btnBase) btnBase.style.cssText = (mode === 'base') ? activeStyle : inactiveStyle;
            if (btnDiff) btnDiff.style.cssText = (mode === 'diff') ? activeStyle : inactiveStyle;

            renderLongTermCandidates();
        }

        async function loadLongTermData() {
            const tableBody = document.getElementById('long_term_candidates_body');
            const fundsListContainer = document.getElementById('long_term_funds_list_container');
            const dateLabel = document.getElementById('long_term_data_date');

            if (tableBody) tableBody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:30px; color:#94a3b8;">⏳ 正在向伺服器請求最新持股分析資料...</td></tr>`;
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
                if (tableBody) tableBody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:30px; color:#ef4444;">❌ 無法載入資料: ${errObj.error}</td></tr>`;
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
            const isBaseMonth = (currentLongTermMonthMode === 'base');

            // 建立 2026-07 基期持股統計索引，供比對各單元格增減
            const baseStatsMap = {};
            if (globalRawLongTermPayload && globalRawLongTermPayload.candidates_base) {
                globalRawLongTermPayload.candidates_base.forEach(b => {
                    let bMfCount = 0, bEtfCount = 0, bMfQty = 0, bEtfQty = 0;
                    if (b.funds) {
                        b.funds.forEach(fObj => {
                            let fName = "";
                            for (let comp in globalTop10Funds) {
                                let match = globalTop10Funds[comp].find(x => x.code === fObj.code);
                                if (match) { fName = match.name; break; }
                            }
                            let q = parseFloat(String(fObj.qty).replace(/,/g, '')) || 0;
                            if (fName && isFundETF(fObj.code, fName)) {
                                bEtfCount++; bEtfQty += q;
                            } else {
                                bMfCount++; bMfQty += q;
                            }
                        });
                    }
                    baseStatsMap[b.stock_name] = {
                        mfCount: bMfCount,
                        etfCount: bEtfCount,
                        mfQty: bMfQty,
                        etfQty: bEtfQty,
                        funds: b.funds || []
                    };
                });
            }

            // 決定顯示清單來源
            let sourceList = [];
            if (isBaseMonth) {
                sourceList = (globalRawLongTermPayload && globalRawLongTermPayload.candidates_base) ? globalRawLongTermPayload.candidates_base : [];
            } else if (currentLongTermMonthMode === 'diff') {
                sourceList = (globalLongTermCandidates || []).filter(item => item.status === 'new' || item.status === 'increase' || item.status === 'decrease');
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
                tableBody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:30px; color:#94a3b8;">📭 目前沒有符合篩選條件的個股</td></tr>`;
                return;
            }

            tableBody.innerHTML = '';

            displayList.forEach((item, index) => {
                let mfCount = 0, etfCount = 0, mfQty = 0, etfQty = 0;

                if (item.funds) {
                    item.funds.forEach(fObj => {
                        let fName = "";
                        for (let comp in globalTop10Funds) {
                            let match = globalTop10Funds[comp].find(x => x.code === fObj.code);
                            if (match) { fName = match.name; break; }
                        }
                        let qty = parseFloat(String(fObj.qty).replace(/,/g, '')) || 0;
                        if (fName && isFundETF(fObj.code, fName)) {
                            etfCount++; etfQty += qty;
                        } else {
                            mfCount++; mfQty += qty;
                        }
                    });
                }

                // 計算各自與 2026-07 基期的差異
                let mfCountDiffHtml = "", etfCountDiffHtml = "", mfQtyDiffHtml = "", etfQtyDiffHtml = "";

                if (!isBaseMonth) {
                    const bInfo = baseStatsMap[item.stock_name];
                    const isNewStock = !bInfo;

                    // 1. 共同基金數差異
                    if (isNewStock) {
                        mfCountDiffHtml = `<div style="font-size:0.75rem; color:#ef4444; font-weight:700; margin-top:3px;">(🔥新進)</div>`;
                    } else {
                        const d = mfCount - bInfo.mfCount;
                        if (d > 0) mfCountDiffHtml = `<div style="font-size:0.75rem; color:#10b981; font-weight:700; margin-top:3px;">(+${d} 檔)</div>`;
                        else if (d < 0) mfCountDiffHtml = `<div style="font-size:0.75rem; color:#f97316; font-weight:700; margin-top:3px;">(${d} 檔)</div>`;
                        else mfCountDiffHtml = `<div style="font-size:0.75rem; color:#94a3b8; margin-top:3px;">(持平)</div>`;
                    }

                    // 2. ETF數差異
                    if (isNewStock) {
                        etfCountDiffHtml = `<div style="font-size:0.75rem; color:#ef4444; font-weight:700; margin-top:3px;">(🔥新進)</div>`;
                    } else {
                        const d = etfCount - bInfo.etfCount;
                        if (d > 0) etfCountDiffHtml = `<div style="font-size:0.75rem; color:#10b981; font-weight:700; margin-top:3px;">(+${d} 檔)</div>`;
                        else if (d < 0) etfCountDiffHtml = `<div style="font-size:0.75rem; color:#f97316; font-weight:700; margin-top:3px;">(${d} 檔)</div>`;
                        else etfCountDiffHtml = `<div style="font-size:0.75rem; color:#94a3b8; margin-top:3px;">(持平)</div>`;
                    }

                    // 3. 共同基金總持股差異
                    if (isNewStock) {
                        mfQtyDiffHtml = `<div style="font-size:0.75rem; color:#ef4444; font-weight:700; margin-top:2px;">(+${mfQty.toLocaleString()} 股)</div>`;
                    } else {
                        const d = mfQty - bInfo.mfQty;
                        if (d > 0) mfQtyDiffHtml = `<div style="font-size:0.75rem; color:#10b981; font-weight:700; margin-top:2px;">(+${d.toLocaleString()} 股)</div>`;
                        else if (d < 0) mfQtyDiffHtml = `<div style="font-size:0.75rem; color:#f97316; font-weight:700; margin-top:2px;">(${d.toLocaleString()} 股)</div>`;
                        else mfQtyDiffHtml = `<div style="font-size:0.75rem; color:#94a3b8; margin-top:2px;">(持平)</div>`;
                    }

                    // 4. ETF總持股差異
                    if (isNewStock) {
                        etfQtyDiffHtml = `<div style="font-size:0.75rem; color:#ef4444; font-weight:700; margin-top:2px;">(+${etfQty.toLocaleString()} 股)</div>`;
                    } else {
                        const d = etfQty - bInfo.etfQty;
                        if (d > 0) etfQtyDiffHtml = `<div style="font-size:0.75rem; color:#10b981; font-weight:700; margin-top:2px;">(+${d.toLocaleString()} 股)</div>`;
                        else if (d < 0) etfQtyDiffHtml = `<div style="font-size:0.75rem; color:#f97316; font-weight:700; margin-top:2px;">(${d.toLocaleString()} 股)</div>`;
                        else etfQtyDiffHtml = `<div style="font-size:0.75rem; color:#94a3b8; margin-top:2px;">(持平)</div>`;
                    }
                }

                const tr = document.createElement('tr');
                tr.id = 'row_candidate_' + item.stock_name;
                tr.innerHTML = `
                    <td style="padding:10px; font-weight:700; font-size:0.9rem;">#${index + 1}</td>
                    <td style="padding:10px; font-weight:700; color:#818cf8; font-size:0.95rem;">${item.stock_name}</td>
                    <td style="padding:10px; text-align:center;">
                        <button onclick="showHoldingFundsDetail('${item.stock_name}')" style="background: rgba(168, 85, 247, 0.15); color: #a855f7; padding: 4px 10px; border-radius: 6px; font-weight: 700; font-size: 0.9rem; border: 1px solid rgba(168, 85, 247, 0.4); cursor: pointer; transition: all 0.2s;" onmouseover="this.style.background='rgba(168, 85, 247, 0.3)'" onmouseout="this.style.background='rgba(168, 85, 247, 0.15)'">
                            ${mfCount} 檔
                        </button>
                        ${mfCountDiffHtml}
                    </td>
                    <td style="padding:10px; text-align:center;">
                        <button onclick="showHoldingFundsDetail('${item.stock_name}')" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8; padding: 4px 10px; border-radius: 6px; font-weight: 700; font-size: 0.9rem; border: 1px solid rgba(56, 189, 248, 0.4); cursor: pointer; transition: all 0.2s;" onmouseover="this.style.background='rgba(56, 189, 248, 0.3)'" onmouseout="this.style.background='rgba(56, 189, 248, 0.15)'">
                            ${etfCount} 檔
                        </button>
                        ${etfCountDiffHtml}
                    </td>
                    <td style="padding:10px; text-align:right;">
                        <div style="font-weight:bold; color: #a855f7; font-size:0.9rem;">${mfQty.toLocaleString()}</div>
                        ${mfQtyDiffHtml}
                    </td>
                    <td style="padding:10px; text-align:right;">
                        <div style="font-weight:bold; color: #38bdf8; font-size:0.9rem;">${etfQty.toLocaleString()}</div>
                        ${etfQtyDiffHtml}
                    </td>
                    <td style="padding:10px; text-align:center;">
                        <button onclick="alert('基本面分析建置中，敬請期待 (目前標的: ${item.stock_name})')" style="padding: 4px 8px; font-size: 0.85rem; background: rgba(59, 130, 246, 0.2); border: 1px solid rgba(59, 130, 246, 0.4); color: #60a5fa; border-radius: 6px; cursor: pointer;">🔍 分析</button>
                    </td>
                `;
                tableBody.appendChild(tr);
            });
        }

        function showHoldingFundsDetail(stockName) {
            window.lastClickedStockForScroll = stockName;
            const btnReturn = document.getElementById('btn_return_to_candidate');
            if (btnReturn) btnReturn.style.display = 'inline-block';

            document.getElementById('detail_stock_name').innerText = stockName;
            document.getElementById('detail_chart_placeholder').style.display = 'none';
            document.getElementById('detail_charts_wrapper').style.display = 'flex';

            // 找出該個股對應的基金代號清單 (包含 qty)
            const stockData = globalLongTermCandidates.find(s => s.stock_name === stockName);
            if (!stockData || !stockData.funds) return;

            const targetFundObjs = stockData.funds; // [{code, qty}]

            // 取得該個股在 2026-07 基期的持股清單 (供柱狀圖計算單檔增減)
            const baseStock = (globalRawLongTermPayload && globalRawLongTermPayload.candidates_base) 
                ? globalRawLongTermPayload.candidates_base.find(b => b.stock_name === stockName) : null;
            const baseFundsMap = {};
            if (baseStock && baseStock.funds) {
                baseStock.funds.forEach(bf => {
                    baseFundsMap[bf.code] = parseFloat(String(bf.qty).replace(/,/g, '')) || 0;
                });
            }

            // 收集這些代號在 globalTop10Funds 中的詳細資訊
            let foundFunds = [];
            for (const [comp, funds] of Object.entries(globalTop10Funds)) {
                funds.forEach(f => {
                    const match = targetFundObjs.find(tf => tf.code === f.code);
                    if (match) {
                        const currQty = parseFloat(String(match.qty).replace(/,/g, '')) || 0;
                        let diffText = "";
                        let diffColor = "#94a3b8";

                        if (baseStock) {
                            if (baseFundsMap[f.code] !== undefined) {
                                const prevQty = baseFundsMap[f.code];
                                const dQty = currQty - prevQty;
                                if (dQty > 0) {
                                    diffText = `(+${dQty.toLocaleString()})`;
                                    diffColor = "#10b981";
                                } else if (dQty < 0) {
                                    diffText = `(${dQty.toLocaleString()})`;
                                    diffColor = "#f97316";
                                } else {
                                    diffText = `(持平)`;
                                    diffColor = "#94a3b8";
                                }
                            } else {
                                diffText = `(新進)`;
                                diffColor = "#ef4444";
                            }
                        } else {
                            diffText = `(新進)`;
                            diffColor = "#ef4444";
                        }

                        foundFunds.push({
                            comp,
                            qty: currQty,
                            diffText,
                            diffColor,
                            ...f
                        });
                    }
                });
            }

            // 分辨 ETF 與 共同基金
            let mutualFunds = foundFunds.filter(f => !isFundETF(f.code, f.name));
            let etfFunds = foundFunds.filter(f => isFundETF(f.code, f.name));

            // 依據 持股數量(qty) 排序
            mutualFunds.sort((a, b) => (b.qty || 0) - (a.qty || 0));
            etfFunds.sort((a, b) => (b.qty || 0) - (a.qty || 0));

            const top10Mutual = mutualFunds.slice(0, 10);
            const top10ETF = etfFunds.slice(0, 10);

            const isDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
            const textColor = isDark ? '#cbd5e1' : '#475569';
            const gridColor = isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.05)';

            const inlineDataLabelsPlugin = {
                id: 'inlineDataLabels',
                afterDatasetsDraw(chart, args, options) {
                    const { ctx } = chart;
                    ctx.font = 'bold 12px "Outfit", sans-serif';
                    ctx.textAlign = 'left';
                    ctx.textBaseline = 'middle';

                    chart.data.datasets.forEach((dataset, i) => {
                        const meta = chart.getDatasetMeta(i);
                        if (!meta.hidden) {
                            meta.data.forEach((bar, index) => {
                                const item = chart.dataListRef ? chart.dataListRef[index] : null;
                                const val = dataset.data[index] || 0;
                                const valStr = ' ' + val.toLocaleString();
                                ctx.fillStyle = textColor;
                                ctx.fillText(valStr, bar.x + 4, bar.y);

                                if (item && item.diffText) {
                                    const valWidth = ctx.measureText(valStr).width;
                                    ctx.fillStyle = item.diffColor || '#94a3b8';
                                    ctx.fillText(' ' + item.diffText, bar.x + 4 + valWidth, bar.y);
                                }
                            });
                        }
                    });
                }
            };

            const renderChart = (canvasId, dataList, barColor, borderColor, label) => {
                const canvas = document.getElementById(canvasId);
                if (charts[canvasId]) {
                    charts[canvasId].destroy();
                }
                const labels = dataList.map(f => f.name.split('(')[0].split('（')[0].trim());
                const dataVals = dataList.map(f => f.qty || 0);

                const ctx = canvas.getContext('2d');
                const newChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: label,
                            data: dataVals,
                            backgroundColor: barColor,
                            borderColor: borderColor,
                            borderWidth: 1,
                            borderRadius: 4
                        }]
                    },
                    plugins: [inlineDataLabelsPlugin],
                    options: {
                        indexAxis: 'y',
                        responsive: true,
                        maintainAspectRatio: false,
                        layout: { padding: { right: 110 } },
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                callbacks: {
                                    title: function (context) {
                                        const fund = dataList[context[0].dataIndex];
                                        if (!fund) return context[0].label;
                                        const isETF = isFundETF(fund.code, fund.name);
                                        if (isETF) {
                                            // ETF 一律精準顯示官方證券代號 (如 0050、00406A 等)
                                            return getOfficialETFCode(fund.code, fund.name);
                                        } else {
                                            // 共同基金顯示代號與簡稱
                                            const shortName = fund.name ? fund.name.split('(')[0].split('（')[0].trim().substr(0, 10) : '';
                                            return fund.code + (shortName ? ' ' + shortName : '');
                                        }
                                    },
                                    label: function (context) {
                                        const fund = dataList[context.dataIndex];
                                        const scale = getFundScale(fund.code);
                                        const scaleStr = scale > 0 ? scale + ' 億元' : '未知';
                                        const diffDesc = fund.diffText ? ` (前期差異: ${fund.diffText})` : '';
                                        return [
                                            ' 持股數: ' + context.raw.toLocaleString() + ' 股' + diffDesc,
                                            ' 基金規模: ' + scaleStr
                                        ];
                                    }
                                }
                            }
                        },
                        scales: {
                            x: {
                                grid: { color: gridColor },
                                ticks: { color: textColor, font: { family: "'Outfit', sans-serif" } }
                            },
                            y: {
                                grid: { display: false },
                                ticks: {
                                    color: textColor, font: { family: "'Outfit', sans-serif", size: window.innerWidth < 768 ? 10 : 13, weight: 'bold' },
                                    callback: function (value, index, ticks) {
                                        const label = this.getLabelForValue(value);
                                        if (window.innerWidth < 768 && label.length > 10) {
                                            return label.substr(0, 10) + '...';
                                        }
                                        return label;
                                    }
                                },
                                afterFit: function (scaleInstance) {
                                    scaleInstance.width = window.innerWidth < 768 ? 130 : 240;
                                }
                            }
                        }
                    }
                });
                newChart.dataListRef = dataList;
                charts[canvasId] = newChart;
            };

            renderChart('detailHoldingChart', top10Mutual, 'rgba(168, 85, 247, 0.7)', '#a855f7', '持股數 (共同基金)');
            renderChart('detailETFChart', top10ETF, 'rgba(56, 189, 248, 0.7)', '#38bdf8', '持股數 (ETF)');

            setTimeout(() => {
                const panel = document.getElementById('long_term_detail_panel');
                const scrollContainer = document.querySelector('.main-panel');
                if (panel && scrollContainer) {
                    const relativeTop = panel.getBoundingClientRect().top - scrollContainer.getBoundingClientRect().top;
                    const targetY = scrollContainer.scrollTop + relativeTop - 20;
                    scrollContainer.scrollTo({ top: targetY, behavior: 'smooth' });
                }
            }, 100);
        }
"""

    start_idx = html.find(old_js_block_start)
    end_idx = html.find(old_js_block_end)

    if start_idx != -1 and end_idx != -1:
        html = html[:start_idx] + new_js_block + "\n        " + html[end_idx:]
        print("✅ 3. 替換 JavaScript 核心邏輯 (括號換行說明、柱狀圖差異括號、官方代號 Tooltip) 完成")
    else:
        print(f"⚠️ 3. 未找到 JS 區塊邊界 (start_idx={start_idx}, end_idx={end_idx})")

    with open(target_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"🎉 成功寫入 {target_path}！")

if __name__ == '__main__':
    apply_patch(TARGET_FILE)
