# -*- coding: utf-8 -*-
"""
================================================================================
  V8.5 網頁 UI 注入腳本 (patch_v8_5_html_ui.py)
  
  用途：讀取原乾淨版本 dashboard_v8_4_backup.html 產生 dashboard_v8_5_backup.html 並注入：
        1. 頂部「🔔 訊號通知中心」與「⚙️ 自動推播設定」按鈕與徽章
        2. 今日三態訊號通知中心 Modal 彈窗 (分區 Table 表格呈現)
        3. 推播設定與即時測試 Modal 彈窗
        4. 前端 JavaScript 三態訊號解析與分區表格渲染邏輯
        5. 「📊 目前策略持倉總覽」表格中加入「🎯 預計停利價」、「🛑 預計停損價」與「今日訊號處置」欄位
        6. 修復將 leaderboard_v8_4.json / trades_v8_4.json 替換為 v8_5，並補齊 activeHoldings 中的 tpPrice 與 slPrice
================================================================================
"""

import os
import sys
import shutil

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

SCRIPT_DIR = r"E:\G-AI-1\Stock analysis"
BASE_V84_PATH = os.path.join(SCRIPT_DIR, "修正版_V6_Server", "public", "dashboard_v8_4_backup.html")
TARGET_V85_BACKUP = os.path.join(SCRIPT_DIR, "修正版_V6_Server", "public", "dashboard_v8_5_backup.html")

def patch():
    if not os.path.exists(BASE_V84_PATH):
        print(f"❌ 找不到 {BASE_V84_PATH}")
        return

    # 複製份全新的 V8.4 Baseline 作為 V8.5 Backup
    shutil.copyfile(BASE_V84_PATH, TARGET_V85_BACKUP)

    with open(TARGET_V85_BACKUP, 'r', encoding='utf-8') as f:
        html = f.read()

    # 0. 全面替換 leaderboard JSON 與 trades JSON 請求路徑為 V8.5
    html = html.replace("leaderboard_v8_4.json", "leaderboard_v8_5.json")
    html = html.replace("trades_v8_4.json", "trades_v8_5.json")

    # 修復 loadLeaderboardData 內部 activeHoldings 賦值，補齊 tpPrice 與 slPrice
    old_active_holding_init = """                    if (item.holding) {
                        activeHoldings[uniqueId] = {
                            code: item.code,
                            name: item.name,
                            buyDate: item.holding.buyDate,
                            buyPrice: item.holding.buyPrice,
                            currentPrice: item.holding.currentPrice || item.holding.buyPrice,
                            pnl: item.holding.pnl || 0,
                            roi: item.holding.roi || 0,
                            shares: item.holding.shares || 1,
                            uniqueId: uniqueId,
                            posType: item.holding.posType || '多單',
                            type: item.type || 'long'
                        };
                    }"""

    new_active_holding_init = """                    if (item.holding) {
                        activeHoldings[uniqueId] = {
                            code: item.code,
                            name: item.name,
                            buyDate: item.holding.buyDate,
                            buyPrice: item.holding.buyPrice,
                            currentPrice: item.holding.currentPrice || item.holding.buyPrice,
                            pnl: item.holding.pnl || 0,
                            roi: item.holding.roi || 0,
                            shares: item.holding.shares || 1,
                            uniqueId: uniqueId,
                            posType: item.holding.posType || '多單',
                            type: item.type || 'long',
                            tpPrice: item.holding.tpPrice || (item.signalInfo ? item.signalInfo.tpPrice : null),
                            slPrice: item.holding.slPrice || (item.signalInfo ? item.signalInfo.slPrice : null)
                        };
                    }"""

    if old_active_holding_init in html:
        html = html.replace(old_active_holding_init, new_active_holding_init, 1)

    # 1. 注入 CSS 樣式
    css_to_insert = """
        /* V8.5 新增：訊號通知中心與推播按鈕樣式 */
        .btn-signal-center {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 7px 14px;
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 700;
            font-size: 0.82rem;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
            transition: all 0.2s ease;
            position: relative;
        }

        .btn-signal-center:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 16px rgba(239, 68, 68, 0.4);
        }

        .signal-badge {
            background: #ffffff;
            color: #dc2626;
            font-size: 0.75rem;
            font-weight: 800;
            padding: 2px 6px;
            border-radius: 10px;
            min-width: 18px;
            text-align: center;
        }

        .btn-push-config {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 7px 14px;
            background: rgba(99, 102, 241, 0.15);
            color: #818cf8;
            border: 1px solid rgba(99, 102, 241, 0.4);
            border-radius: 8px;
            font-weight: 600;
            font-size: 0.82rem;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .btn-push-config:hover {
            background: #6366f1;
            color: white;
        }

        /* 訊號表格容器 */
        .signal-table-wrapper {
            max-height: 480px;
            overflow-y: auto;
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            margin-top: 15px;
        }

        .signal-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.84rem;
            text-align: left;
        }

        .signal-table th {
            background: #1e293b;
            color: #94a3b8;
            padding: 12px 10px;
            font-weight: 700;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            position: sticky;
            top: 0;
            z-index: 2;
        }

        .signal-table td {
            padding: 10px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            color: #e2e8f0;
        }

        .signal-table tr:hover {
            background: rgba(255, 255, 255, 0.03);
        }

        .signal-tag {
            font-size: 0.72rem;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 6px;
            display: inline-block;
        }

        .tag-entry { background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.4); }
        .tag-exit-tp { background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.4); }
        .tag-exit-sl { background: rgba(239, 68, 68, 0.25); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.5); }
        .tag-exit-sig { background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.4); }
        .tag-holding { background: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.4); }

        .signal-tabs {
            display: flex;
            gap: 10px;
            border-bottom: 1px solid var(--border);
            padding-bottom: 10px;
            margin-bottom: 15px;
        }

        .signal-tab-btn {
            padding: 8px 16px;
            background: transparent;
            border: none;
            color: #94a3b8;
            font-weight: 600;
            font-size: 0.9rem;
            cursor: pointer;
            border-radius: 6px;
            transition: all 0.2s;
        }

        .signal-tab-btn.active {
            background: rgba(99, 102, 241, 0.2);
            color: #818cf8;
        }
    """

    style_idx = html.find("</style>")
    if style_idx != -1:
        html = html[:style_idx] + css_to_insert + "\n" + html[style_idx:]

    # 2. 注入按鈕至使用者資訊區塊 (user-profile-card)
    btn_html = """
            <div style="margin-top: 12px; display: flex; gap: 8px; flex-wrap: wrap;">
                <button class="btn-signal-center" onclick="openSignalCenterModal()">
                    🔔 訊號通知中心 <span id="badge_signal_count" class="signal-badge">0</span>
                </button>
                <button class="btn-push-config" onclick="openPushSettingsModal()">
                    ⚙️ 推播設定
                </button>
            </div>
    """
    profile_idx = html.find('<div class="user-profile-card">')
    if profile_idx != -1:
        end_card_idx = html.find('</div>', profile_idx + 30)
        if end_card_idx != -1:
            html = html[:end_card_idx] + btn_html + html[end_card_idx:]

    # 3. 更新「目前策略持倉總覽」表格標頭 (加入 停利價、停損價、今日訊號處置 欄位)
    old_th_str = '<th style="padding:12px; font-weight:700;">操作</th>'
    new_th_str = """<th style="padding:12px; font-weight:700; color:#4ade80;">🎯 預計停利價</th>
                            <th style="padding:12px; font-weight:700; color:#f87171;">🛑 預計停損價</th>
                            <th style="padding:12px; font-weight:700;">今日訊號處置</th>
                            <th style="padding:12px; font-weight:700;">操作</th>"""
    if old_th_str in html:
        html = html.replace(old_th_str, new_th_str, 1)

    # 4. 注入 Modal 彈窗 HTML
    modals_html = """
    <!-- V8.5 新增：今日三態訊號通知中心 Modal (表格呈現) -->
    <div id="modal_signal_center" class="modal" style="display: none; position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.7); z-index: 9999; justify-content: center; align-items: center;">
        <div style="background: #0f172a; border: 1px solid rgba(255,255,255,0.1); width: 92%; max-width: 1050px; border-radius: 16px; padding: 24px; color: #f8fafc; box-shadow: 0 20px 40px rgba(0,0,0,0.5);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                <h3 style="font-size: 1.25rem; font-weight: 700; color: #818cf8; display: flex; align-items: center; gap: 8px;">
                    🔔 今日三態選股與觸發訊號通知中心 (表格明細)
                </h3>
                <span onclick="closeSignalCenterModal()" style="cursor: pointer; font-size: 1.5rem; color: #94a3b8;">&times;</span>
            </div>

            <div class="signal-tabs">
                <button id="btn_tab_entry" class="signal-tab-btn active" onclick="switchSignalTab('ENTRY')">
                    🔥 今日剛觸發進場 (<span id="cnt_entry">0</span>)
                </button>
                <button id="btn_tab_exit" class="signal-tab-btn" onclick="switchSignalTab('EXIT')">
                    ⚠️ 今日剛觸發離場 (<span id="cnt_exit">0</span>)
                </button>
                <button id="btn_tab_holding" class="signal-tab-btn" onclick="switchSignalTab('HOLDING')">
                    📦 現正持倉總覽 (<span id="cnt_holding">0</span>)
                </button>
            </div>

            <div id="signal_cards_container">
                <!-- 動態注入訊號分區表格 -->
            </div>
            
            <div style="margin-top: 20px; text-align: right;">
                <button onclick="closeSignalCenterModal()" style="padding: 8px 20px; background: #334155; border: none; border-radius: 8px; color: white; cursor: pointer; font-weight: 600;">關閉</button>
            </div>
        </div>
    </div>

    <!-- V8.5 新增：自動推播設定與測試 Modal -->
    <div id="modal_push_settings" class="modal" style="display: none; position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.7); z-index: 9999; justify-content: center; align-items: center;">
        <div style="background: #0f172a; border: 1px solid rgba(255,255,255,0.1); width: 90%; max-width: 550px; border-radius: 16px; padding: 24px; color: #f8fafc; box-shadow: 0 20px 40px rgba(0,0,0,0.5);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                <h3 style="font-size: 1.15rem; font-weight: 700; color: #818cf8; display: flex; align-items: center; gap: 8px;">
                    ⚙️ 自動推播連線狀態與設定
                </h3>
                <span onclick="closePushSettingsModal()" style="cursor: pointer; font-size: 1.5rem; color: #94a3b8;">&times;</span>
            </div>

            <div style="background: rgba(30, 41, 59, 0.5); padding: 16px; border-radius: 12px; margin-bottom: 16px; font-size: 0.88rem; line-height: 1.6;">
                <p style="color: #4ade80; font-weight: 700; margin-bottom: 6px;">🟢 LINE Bot 廣播已連線就緒 (Channel ID: 2011494352)</p>
                <p style="color: #94a3b8;">系統會於每日 <code style="color: #cbd5e1;">update_and_push_v8_5.py</code> 自動更新完成時，自動發送最新選股與觸發訊號至您的 LINE！</p>
            </div>

            <div style="text-align: center; margin-top: 20px; display: flex; gap: 10px; justify-content: flex-end;">
                <button onclick="testLinePushWeb()" style="padding: 8px 16px; background: #22c55e; border: none; border-radius: 8px; color: white; font-weight: 700; cursor: pointer;">🧪 發送 LINE 測試連線</button>
                <button onclick="closePushSettingsModal()" style="padding: 8px 16px; background: #334155; border: none; border-radius: 8px; color: white; cursor: pointer; font-weight: 600;">確定</button>
            </div>
        </div>
    </div>
    """

    body_end_idx = html.find("</body>")
    if body_end_idx != -1:
        html = html[:body_end_idx] + modals_html + "\n" + html[body_end_idx:]

    # 5. 更新 updateHoldingSummaryPanel 渲染邏輯 (含自動補齊計算停利/停損價)
    old_panel_func = """            if (holdings.length === 0) {
                tableBody.innerHTML = `<tr><td colspan="9" style="text-align:center; padding:15px; color:var(--text-muted);">📭 目前無策略持倉</td></tr>`;
            } else {
                tableBody.innerHTML = holdings.map(h => {
                    const isWin = h.pnl >= 0;
                    const sign = isWin ? '+' : '';
                    const color = isWin ? '#10b981' : '#ef4444';

                    const typeText = h.posType || '多單';
                    const isShort = typeText === '空單';
                    const icon = isShort ? '📉' : '📈';

                    return `
                        <tr>
                            <td><input type="checkbox" class="holding-checkbox" checked onchange="calculateHoldingTotalPnl()" data-pnl="${h.pnl}" data-cost="${h.buyPrice * h.shares * 1000}"></td>
                            <td><span style="font-size:0.8rem; font-weight:700; padding:3px 8px; border-radius:4px; background:${isShort ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)'}; color:${isShort ? '#10b981' : '#ef4444'};">${icon} ${typeText}</span></td>
                            <td style="font-weight:700;">${h.code} ${h.name}</td>
                            <td>${h.buyDate}</td>
                            <td>$${h.buyPrice.toFixed(1)}</td>
                            <td>$${h.currentPrice.toFixed(1)}</td>
                            <td>${h.shares}</td>
                            <td style="color:${color}; font-weight:700;">${sign}$${Math.round(h.pnl).toLocaleString()} <br><small>(${sign}${h.roi.toFixed(2)}%)</small></td>
                            <td>
                                <button class="tab-btn" style="padding: 4px 10px; font-size: 0.8rem; background: #6366f1; border: none; border-radius: 4px; color: white; cursor: pointer;" onclick="selectStockTab('${h.uniqueId}', '${h.uniqueId}', '${h.name}', '${getStrategyIdByUniqueId(h.uniqueId)}', '${h.uniqueId.startsWith('custom_') ? 'custom' : 'preload'}')">查看</button>
                            </td>
                        </tr>
                    `;
                }).join('');
            }"""

    new_panel_func = """            if (holdings.length === 0) {
                tableBody.innerHTML = `<tr><td colspan="12" style="text-align:center; padding:15px; color:var(--text-muted);">📭 目前無策略持倉</td></tr>`;
            } else {
                tableBody.innerHTML = holdings.map(h => {
                    const isWin = h.pnl >= 0;
                    const sign = isWin ? '+' : '';
                    const color = isWin ? '#10b981' : '#ef4444';

                    const typeText = h.posType || '多單';
                    const isShort = typeText === '空單';
                    const icon = isShort ? '📉' : '📈';

                    const buyP = h.buyPrice || 0;
                    const stockObj = (typeof preloadedStocks !== 'undefined') ? preloadedStocks.find(s => s.id.replace('s','').replace('_ai','') === h.code) : null;
                    const sigObj = stockObj ? stockObj.signalInfo : null;

                    let rawTp = h.tpPrice || (sigObj ? sigObj.tpPrice : null);
                    let rawSl = h.slPrice || (sigObj ? sigObj.slPrice : null);
                    let tpPct = (stockObj && stockObj.tp) ? stockObj.tp : 6.0;
                    let slPct = (stockObj && stockObj.sl) ? stockObj.sl : 6.0;

                    let tpVal = rawTp ? rawTp : (buyP > 0 ? buyP * (1 + (isShort ? -1 : 1) * (tpPct / 100)) : 0);
                    let slVal = rawSl ? rawSl : (buyP > 0 ? buyP * (1 + (isShort ? 1 : -1) * (slPct / 100)) : 0);

                    const tpText = tpVal > 0 ? `$${tpVal.toFixed(1)} (${isShort ? '-' : '+'}${tpPct}%)` : '-';
                    const slText = slVal > 0 ? `$${slVal.toFixed(1)} (${isShort ? '+' : '-'}${slPct}%)` : '-';

                    let sigTag = '<span style="font-size:0.75rem; font-weight:700; padding:2px 6px; border-radius:4px; background:rgba(59,130,246,0.2); color:#60a5fa;">📦 續抱中</span>';
                    if (stockObj && stockObj.signalInfo && stockObj.signalInfo.status === 'TRIGGER_EXIT') {
                        const sig = stockObj.signalInfo;
                        if (sig.exitReasonType === 'TAKE_PROFIT') {
                            sigTag = '<span style="font-size:0.75rem; font-weight:700; padding:2px 6px; border-radius:4px; background:rgba(16,185,129,0.2); color:#34d399;">🎯 達標停利(明日平倉)</span>';
                        } else if (sig.exitReasonType === 'STOP_LOSS') {
                            sigTag = '<span style="font-size:0.75rem; font-weight:700; padding:2px 6px; border-radius:4px; background:rgba(239,68,68,0.25); color:#f87171;">🛑 觸發停損(明日平倉)</span>';
                        } else {
                            sigTag = '<span style="font-size:0.75rem; font-weight:700; padding:2px 6px; border-radius:4px; background:rgba(245,158,11,0.2); color:#fbbf24;">⚠️ 指標離場(明日平倉)</span>';
                        }
                    }

                    return `
                        <tr>
                            <td><input type="checkbox" class="holding-checkbox" checked onchange="calculateHoldingTotalPnl()" data-pnl="${h.pnl}" data-cost="${h.buyPrice * h.shares * 1000}"></td>
                            <td><span style="font-size:0.8rem; font-weight:700; padding:3px 8px; border-radius:4px; background:${isShort ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)'}; color:${isShort ? '#10b981' : '#ef4444'};">${icon} ${typeText}</span></td>
                            <td style="font-weight:700;">${h.code} ${h.name}</td>
                            <td>${h.buyDate}</td>
                            <td>$${h.buyPrice.toFixed(1)}</td>
                            <td>$${h.currentPrice.toFixed(1)}</td>
                            <td>${h.shares}</td>
                            <td style="color:${color}; font-weight:700;">${sign}$${Math.round(h.pnl).toLocaleString()} <br><small>(${sign}${h.roi.toFixed(2)}%)</small></td>
                            <td style="color:#4ade80; font-weight:700;">${tpText}</td>
                            <td style="color:#f87171; font-weight:700;">${slText}</td>
                            <td>${sigTag}</td>
                            <td>
                                <button class="tab-btn" style="padding: 4px 10px; font-size: 0.8rem; background: #6366f1; border: none; border-radius: 4px; color: white; cursor: pointer;" onclick="selectStockTab('${h.uniqueId}', '${h.uniqueId}', '${h.name}', '${getStrategyIdByUniqueId(h.uniqueId)}', '${h.uniqueId.startsWith('custom_') ? 'custom' : 'preload'}')">查看</button>
                            </td>
                        </tr>
                    `;
                }).join('');
            }"""

    if old_panel_func in html:
        html = html.replace(old_panel_func, new_panel_func, 1)

    # 6. 注入 JavaScript 邏輯 (表格呈現與停利停損價智慧計算)
    js_to_insert = """
        // V8.5 三態訊號通知中心與表格渲染邏輯
        let currentSignalTab = 'ENTRY';

        function initV85SignalCenter() {
            if (typeof preloadedStocks === 'undefined') return;
            
            let entryCnt = 0;
            let exitCnt = 0;
            let holdingCnt = 0;

            preloadedStocks.forEach(s => {
                if (s.signalInfo) {
                    if (s.signalInfo.status === 'TRIGGER_ENTRY') entryCnt++;
                    else if (s.signalInfo.status === 'TRIGGER_EXIT') exitCnt++;
                    else if (s.signalInfo.status === 'HOLDING') holdingCnt++;
                }
            });

            const totalActive = entryCnt + exitCnt;
            const badgeEl = document.getElementById('badge_signal_count');
            if (badgeEl) {
                badgeEl.innerText = totalActive;
                badgeEl.style.display = totalActive > 0 ? 'inline-block' : 'none';
            }

            const cEntry = document.getElementById('cnt_entry');
            const cExit = document.getElementById('cnt_exit');
            const cHolding = document.getElementById('cnt_holding');
            if (cEntry) cEntry.innerText = entryCnt;
            if (cExit) cExit.innerText = exitCnt;
            if (cHolding) cHolding.innerText = holdingCnt;
        }

        function openSignalCenterModal() {
            const m = document.getElementById('modal_signal_center');
            if (m) {
                m.style.display = 'flex';
                renderSignalCards(currentSignalTab);
            }
        }

        function closeSignalCenterModal() {
            const m = document.getElementById('modal_signal_center');
            if (m) m.style.display = 'none';
        }

        function openPushSettingsModal() {
            const m = document.getElementById('modal_push_settings');
            if (m) m.style.display = 'flex';
        }

        function closePushSettingsModal() {
            const m = document.getElementById('modal_push_settings');
            if (m) m.style.display = 'none';
        }

        function switchSignalTab(tab) {
            currentSignalTab = tab;
            ['ENTRY', 'EXIT', 'HOLDING'].forEach(t => {
                const btn = document.getElementById('btn_tab_' + t.toLowerCase());
                if (btn) {
                    if (t === tab) btn.classList.add('active');
                    else btn.classList.remove('active');
                }
            });
            renderSignalCards(tab);
        }

        function renderSignalCards(tab) {
            const container = document.getElementById('signal_cards_container');
            if (!container || typeof preloadedStocks === 'undefined') return;
            container.innerHTML = '';

            const filtered = preloadedStocks.filter(s => {
                if (!s.signalInfo) return false;
                if (tab === 'ENTRY') return s.signalInfo.status === 'TRIGGER_ENTRY';
                if (tab === 'EXIT') return s.signalInfo.status === 'TRIGGER_EXIT';
                if (tab === 'HOLDING') return s.signalInfo.status === 'HOLDING';
                return false;
            });

            if (filtered.length === 0) {
                container.innerHTML = `<div style="text-align: center; padding: 40px; color: #94a3b8;">此分類今日尚無紀錄</div>`;
                return;
            }

            let tableHtml = '<div class="signal-table-wrapper"><table class="signal-table"><thead><tr>';

            if (tab === 'ENTRY') {
                tableHtml += `
                    <th>股票標的</th>
                    <th>類型</th>
                    <th>型態策略</th>
                    <th>觸發日期</th>
                    <th>參考買價</th>
                    <th style="color: #4ade80;">🎯 預計停利價</th>
                    <th style="color: #f87171;">🛑 預計停損價</th>
                    <th>預計處置</th>
                </tr></thead><tbody>`;

                filtered.forEach(s => {
                    const sig = s.signalInfo;
                    const stockCode = s.id.replace('s','').replace('_ai','');
                    const dir = sig.direction || (s.type === 'short' ? '空單' : '多單');
                    const isShort = dir === '空單';
                    const icon = isShort ? '📉' : '📈';
                    
                    const buyP = sig.targetEntryPrice || sig.currentPrice || s.buyPrice || 0;
                    let rawTp = sig.tpPrice;
                    let rawSl = sig.slPrice;
                    let tpPct = s.tp || 6.0;
                    let slPct = s.sl || 6.0;

                    let tpVal = rawTp ? rawTp : (buyP > 0 ? buyP * (1 + (isShort ? -1 : 1) * (tpPct / 100)) : 0);
                    let slVal = rawSl ? rawSl : (buyP > 0 ? buyP * (1 + (isShort ? 1 : -1) * (slPct / 100)) : 0);

                    const tpText = tpVal > 0 ? `$${tpVal.toFixed(1)} (${isShort ? '-' : '+'}${tpPct}%)` : '-';
                    const slText = slVal > 0 ? `$${slVal.toFixed(1)} (${isShort ? '+' : '-'}${slPct}%)` : '-';

                    tableHtml += `
                        <tr>
                            <td style="font-weight:700; color:#f8fafc;">${stockCode} ${s.name}</td>
                            <td><span style="color:${isShort ? '#10b981' : '#ef4444'}; font-weight:600;">${icon} ${dir}</span></td>
                            <td style="color:#818cf8; font-weight:600;">${s.entry || s.strategy}</td>
                            <td>${sig.triggerDate || '-'}</td>
                            <td style="font-weight:700;">$${buyP.toFixed(1)}</td>
                            <td style="color:#4ade80; font-weight:700;">${tpText}</td>
                            <td style="color:#f87171; font-weight:700;">${slText}</td>
                            <td><span class="signal-tag tag-entry">🎯 明日開盤預計買進</span></td>
                        </tr>
                    `;
                });
            } else if (tab === 'EXIT') {
                tableHtml += `
                    <th>股票標的</th>
                    <th>類型</th>
                    <th>原買入日</th>
                    <th>原買價</th>
                    <th>當前收盤價</th>
                    <th>累積未實現ROI</th>
                    <th>離場原因細分</th>
                    <th>預計處置</th>
                </tr></thead><tbody>`;

                filtered.forEach(s => {
                    const sig = s.signalInfo;
                    const stockCode = s.id.replace('s','').replace('_ai','');
                    const dir = sig.direction || (s.type === 'short' ? '空單' : '多單');
                    const isShort = dir === '空單';
                    const icon = isShort ? '📉' : '📈';
                    const roiVal = sig.roi || 0;
                    const isWin = roiVal >= 0;
                    const color = isWin ? '#10b981' : '#ef4444';
                    
                    let reasonTag = '<span class="signal-tag tag-exit-sig">📊 指標出場</span>';
                    if (sig.exitReasonType === 'TAKE_PROFIT') {
                        reasonTag = '<span class="signal-tag tag-exit-tp">🎯 達標停利</span>';
                    } else if (sig.exitReasonType === 'STOP_LOSS') {
                        reasonTag = '<span class="signal-tag tag-exit-sl">🛑 觸發停損</span>';
                    }

                    tableHtml += `
                        <tr>
                            <td style="font-weight:700; color:#f8fafc;">${stockCode} ${s.name}</td>
                            <td><span style="color:${isShort ? '#10b981' : '#ef4444'}; font-weight:600;">${icon} ${dir}</span></td>
                            <td>${sig.triggerDate || s.holding?.buyDate || '-'}</td>
                            <td>$${(sig.entryPrice || s.holding?.buyPrice || 0).toFixed(1)}</td>
                            <td>$${(sig.currentPrice || s.holding?.currentPrice || 0).toFixed(1)}</td>
                            <td style="color:${color}; font-weight:700;">${isWin ? '+' : ''}${roiVal.toFixed(2)}%</td>
                            <td>${reasonTag} <span style="font-size:0.75rem; color:#94a3b8;">(${sig.exitReasonText || sig.reason || ''})</span></td>
                            <td><span class="signal-tag tag-exit-sl">⚠️ 明日開盤預計平倉</span></td>
                        </tr>
                    `;
                });
            } else if (tab === 'HOLDING') {
                tableHtml += `
                    <th>股票標的</th>
                    <th>類型</th>
                    <th>買入日期</th>
                    <th>買入成本價</th>
                    <th>當前最新價</th>
                    <th>未實現ROI</th>
                    <th style="color: #4ade80;">🎯 預計停利價</th>
                    <th style="color: #f87171;">🛑 預計停損價</th>
                    <th>當前狀態</th>
                </tr></thead><tbody>`;

                filtered.forEach(s => {
                    const sig = s.signalInfo;
                    const stockCode = s.id.replace('s','').replace('_ai','');
                    const dir = sig.direction || (s.type === 'short' ? '空單' : '多單');
                    const isShort = dir === '空單';
                    const icon = isShort ? '📉' : '📈';
                    const buyP = sig.buyPrice || s.holding?.buyPrice || 0;
                    const currP = sig.currentPrice || s.holding?.currentPrice || 0;
                    const roiVal = sig.roi || s.holding?.roi || 0;
                    const isWin = roiVal >= 0;
                    const color = isWin ? '#10b981' : '#ef4444';

                    let rawTp = sig.tpPrice || s.holding?.tpPrice;
                    let rawSl = sig.slPrice || s.holding?.slPrice;
                    let tpPct = s.tp || 6.0;
                    let slPct = s.sl || 6.0;

                    let tpVal = rawTp ? rawTp : (buyP > 0 ? buyP * (1 + (isShort ? -1 : 1) * (tpPct / 100)) : 0);
                    let slVal = rawSl ? rawSl : (buyP > 0 ? buyP * (1 + (isShort ? 1 : -1) * (slPct / 100)) : 0);

                    const tpText = tpVal > 0 ? `$${tpVal.toFixed(1)} (${isShort ? '-' : '+'}${tpPct}%)` : '-';
                    const slText = slVal > 0 ? `$${slVal.toFixed(1)} (${isShort ? '+' : '-'}${slPct}%)` : '-';

                    tableHtml += `
                        <tr>
                            <td style="font-weight:700; color:#f8fafc;">${stockCode} ${s.name}</td>
                            <td><span style="color:${isShort ? '#10b981' : '#ef4444'}; font-weight:600;">${icon} ${dir}</span></td>
                            <td>${sig.buyDate || s.holding?.buyDate || '-'}</td>
                            <td>$${buyP.toFixed(1)}</td>
                            <td>$${currP.toFixed(1)}</td>
                            <td style="color:${color}; font-weight:700;">${isWin ? '+' : ''}${roiVal.toFixed(2)}%</td>
                            <td style="color:#4ade80; font-weight:700;">${tpText}</td>
                            <td style="color:#f87171; font-weight:700;">${slText}</td>
                            <td><span class="signal-tag tag-holding">📦 續抱中</span></td>
                        </tr>
                    `;
                });
            }

            tableHtml += `</tbody></table></div>`;
            container.innerHTML = tableHtml;
        }

        async function testLinePushWeb() {
            alert("正在發送 LINE 測試廣播...");
            try {
                const res = await fetch('/api/alerts/push', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        channel: 'line_broadcast',
                        message: '🚀 【股票量化分析 V8.5】網頁測試連線廣播成功！'
                    })
                });
                const data = await res.json();
                if (data.success) {
                    alert("🎉 LINE 推播發送成功！");
                } else {
                    alert("⚠️ 推播結果：" + JSON.stringify(data));
                }
            } catch (err) {
                alert("❌ 推播發送錯誤：" + err.message);
            }
        }

        document.addEventListener('DOMContentLoaded', () => {
            setTimeout(initV85SignalCenter, 500);
        });
    """

    script_idx = html.rfind("</script>")
    if script_idx != -1:
        html = html[:script_idx] + js_to_insert + "\n" + html[script_idx:]

    with open(TARGET_V85_BACKUP, 'w', encoding='utf-8') as f:
        f.write(html)
    print("✅ 成功產生乾淨且完全升級之 dashboard_v8_5_backup.html (修復 leaderboard_v8_5.json 請求與停利停損價自動補齊計算)！")

if __name__ == "__main__":
    patch()
