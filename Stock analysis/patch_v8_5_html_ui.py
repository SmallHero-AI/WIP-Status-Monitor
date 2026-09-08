# -*- coding: utf-8 -*-
"""
================================================================================
  V8.5 網頁 UI 注入腳本 (patch_v8_5_html_ui.py)
  
  用途：在 dashboard_v8_5_backup.html 中新增：
        1. 頂部「🔔 訊號通知中心」與「⚙️ 自動推播設定」按鈕與徽章
        2. 今日三態訊號通知中心 Modal 彈窗 (含進場/出場/持倉頁籤)
        3. 推播設定與即時測試 Modal 彈窗
        4. 前端 JavaScript 三態訊號解析與渲染邏輯
================================================================================
"""

import os
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

SCRIPT_DIR = r"E:\G-AI-1\Stock analysis"
BACKUP_PATH = os.path.join(SCRIPT_DIR, "修正版_V6_Server", "public", "dashboard_v8_5_backup.html")

def patch():
    if not os.path.exists(BACKUP_PATH):
        print(f"❌ 找不到 {BACKUP_PATH}")
        return

    with open(BACKUP_PATH, 'r', encoding='utf-8') as f:
        html = f.read()

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

        /* 訊號卡片容器 */
        .signal-cards-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 14px;
            margin-top: 15px;
            max-height: 480px;
            overflow-y: auto;
            padding-right: 4px;
        }

        .signal-card {
            background: rgba(30, 41, 59, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 14px;
            transition: all 0.2s ease;
            position: relative;
        }

        .signal-card:hover {
            border-color: rgba(99, 102, 241, 0.5);
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.3);
        }

        .signal-card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }

        .signal-stock-title {
            font-size: 1.05rem;
            font-weight: 700;
            color: #f8fafc;
        }

        .signal-tag {
            font-size: 0.72rem;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 6px;
        }

        .tag-entry { background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.4); }
        .tag-exit { background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.4); }
        .tag-holding { background: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.4); }

        .signal-detail-item {
            font-size: 0.83rem;
            color: #94a3b8;
            margin-bottom: 4px;
            display: flex;
            justify-content: space-between;
        }

        .signal-detail-val {
            font-weight: 600;
            color: #e2e8f0;
        }

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

    if "/* V8.5 新增：訊號通知中心與推播按鈕樣式 */" not in html:
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
    if "openSignalCenterModal()" not in html:
        profile_idx = html.find('<div class="user-profile-card">')
        if profile_idx != -1:
            end_card_idx = html.find('</div>', profile_idx + 30)
            if end_card_idx != -1:
                html = html[:end_card_idx] + btn_html + html[end_card_idx:]

    # 3. 注入 Modal 彈窗 HTML
    modals_html = """
    <!-- V8.5 新增：今日三態訊號通知中心 Modal -->
    <div id="modal_signal_center" class="modal" style="display: none; position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.7); z-index: 9999; justify-content: center; align-items: center;">
        <div style="background: #0f172a; border: 1px solid rgba(255,255,255,0.1); width: 90%; max-width: 900px; border-radius: 16px; padding: 24px; color: #f8fafc; box-shadow: 0 20px 40px rgba(0,0,0,0.5);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                <h3 style="font-size: 1.25rem; font-weight: 700; color: #818cf8; display: flex; align-items: center; gap: 8px;">
                    🔔 今日三態選股與觸發訊號通知中心
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

            <div id="signal_cards_container" class="signal-cards-grid">
                <!-- 動態注入訊號卡片 -->
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
                <p style="color: #94a3b8;">系統會於每日 <code style="color: #cbd5e1;">update_and_push_v8_5.py</code> 自動更新完成時，自動發送最新選股與觸發卡片至您的 LINE！</p>
            </div>

            <div style="text-align: center; margin-top: 20px; display: flex; gap: 10px; justify-content: flex-end;">
                <button onclick="testLinePushWeb()" style="padding: 8px 16px; background: #22c55e; border: none; border-radius: 8px; color: white; font-weight: 700; cursor: pointer;">🧪 發送 LINE 測試連線</button>
                <button onclick="closePushSettingsModal()" style="padding: 8px 16px; background: #334155; border: none; border-radius: 8px; color: white; cursor: pointer; font-weight: 600;">確定</button>
            </div>
        </div>
    </div>
    """

    if "modal_signal_center" not in html:
        body_end_idx = html.find("</body>")
        if body_end_idx != -1:
            html = html[:body_end_idx] + modals_html + "\n" + html[body_end_idx:]

    # 4. 注入 JavaScript 邏輯
    js_to_insert = """
        // V8.5 三態訊號通知中心邏輯
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
                container.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: #94a3b8;">此分類今日尚無紀錄</div>`;
                return;
            }

            filtered.forEach(s => {
                const sig = s.signalInfo;
                const dir = sig.direction || (s.type === 'short' ? '空單' : '多單');
                const isShort = dir === '空單';
                
                let tagClass = 'tag-entry';
                let tagText = '🔥 今日觸發進場';
                if (sig.status === 'TRIGGER_EXIT') { tagClass = 'tag-exit'; tagText = '⚠️ 今日觸發出場'; }
                else if (sig.status === 'HOLDING') { tagClass = 'tag-holding'; tagText = '📦 持倉中'; }

                const cardHtml = `
                    <div class="signal-card">
                        <div class="signal-card-header">
                            <span class="signal-stock-title">${s.id.replace('s','').replace('_ai','')} ${s.name} (${dir})</span>
                            <span class="signal-tag ${tagClass}">${tagText}</span>
                        </div>
                        <div style="font-size: 0.78rem; color: #818cf8; margin-bottom: 8px; font-weight: 600;">
                            型態策略：${s.entry || s.strategy}
                        </div>
                        <div class="signal-detail-item">
                            <span>觸發日期：</span>
                            <span class="signal-detail-val">${sig.triggerDate || sig.buyDate || '-'}</span>
                        </div>
                        <div class="signal-detail-item">
                            <span>預計進/當前價：</span>
                            <span class="signal-detail-val">$${sig.targetEntryPrice || sig.buyPrice || sig.currentPrice || '-'}</span>
                        </div>
                        <div class="signal-detail-item">
                            <span>目標停利/停損：</span>
                            <span class="signal-detail-val" style="color: #4ade80;">+$${sig.tpPrice || '-'} / -$${sig.slPrice || '-'}</span>
                        </div>
                        <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 6px; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 6px;">
                            ${sig.reason || '策略條件達成'}
                        </div>
                    </div>
                `;
                container.innerHTML += cardHtml;
            });
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

    if "function initV85SignalCenter()" not in html:
        script_idx = html.rfind("</script>")
        if script_idx != -1:
            html = html[:script_idx] + js_to_insert + "\n" + html[script_idx:]

    with open(BACKUP_PATH, 'w', encoding='utf-8') as f:
        f.write(html)
    print("✅ 成功為 dashboard_v8_5_backup.html 注入 V8.5 三態訊號通知中心與 UI 組件！")

if __name__ == "__main__":
    patch()
