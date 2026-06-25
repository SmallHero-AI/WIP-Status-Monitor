
# ── V8.1 Injection Variables ──
NEW_HTML_CONTENT = """        <!-- 📈 策略進出場成績總覽頁面 (V8.1) -->
        <div id="tab_overview" class="page" style="max-width: 1280px; margin: 0 auto;">
            <style>
                /* 策略進出場成績總覽自訂樣式 (V8.1) */
                .overview-container {
                    display: flex;
                    gap: 25px;
                    margin-top: 20px;
                }
                .overview-sidebar {
                    flex: 0 0 300px;
                    border-radius: 12px;
                    padding: 15px;
                    display: flex;
                    flex-direction: column;
                    gap: 12px;
                    max-height: 700px;
                    overflow-y: auto;
                }
                .overview-main {
                    flex: 1;
                    display: flex;
                    flex-direction: column;
                    gap: 20px;
                }
                
                /* 主題自適應 */
                .main-panel.light-theme .overview-sidebar {
                    background: #f8fafc;
                    border: 1px solid #cbd5e1;
                }
                .main-panel.dark-theme .overview-sidebar {
                    background: rgba(30, 41, 59, 0.4);
                    border: 1px solid rgba(255, 255, 255, 0.08);
                }
                
                .main-panel.light-theme #tab_overview {
                    background: #ffffff;
                    color: #0f172a;
                    padding: 30px;
                    border-radius: 16px;
                    box-shadow: 0 10px 25px rgba(0,0,0,0.05);
                }
                .main-panel.dark-theme #tab_overview {
                    background: #1e293b;
                    color: #f8fafc;
                    padding: 30px;
                    border-radius: 16px;
                    box-shadow: 0 10px 25px rgba(0,0,0,0.3);
                }
                
                .main-panel.light-theme .overview-stock-item {
                    background: #ffffff;
                    border: 1px solid #e2e8f0;
                    color: #334155;
                }
                .main-panel.dark-theme .overview-stock-item {
                    background: rgba(15, 23, 42, 0.6);
                    border: 1px solid rgba(255, 255, 255, 0.06);
                    color: #cbd5e1;
                }
                
                .overview-stock-item {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    padding: 10px 12px;
                    border-radius: 8px;
                    cursor: pointer;
                    transition: all 0.2s;
                }
                .overview-stock-item:hover {
                    transform: translateY(-1px);
                    box-shadow: 0 4px 6px rgba(0,0,0,0.05);
                }
                
                .overview-stock-item input[type="checkbox"] {
                    width: 16px;
                    height: 16px;
                    accent-color: var(--primary);
                    cursor: pointer;
                }
                
                /* 搜尋與快速選取按鈕 */
                .overview-search-box {
                    width: 100%;
                    padding: 8px 12px;
                    border-radius: 8px;
                    font-size: 0.85rem;
                    outline: none;
                    transition: border-color 0.2s;
                }
                .main-panel.light-theme .overview-search-box {
                    border: 1px solid #cbd5e1;
                    background: #ffffff;
                    color: #0f172a;
                }
                .main-panel.dark-theme .overview-search-box {
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    background: rgba(15, 23, 42, 0.8);
                    color: #f8fafc;
                }
                
                .overview-quick-btn {
                    padding: 5px 8px;
                    border-radius: 6px;
                    font-size: 0.75rem;
                    font-weight: 600;
                    cursor: pointer;
                    border: none;
                    transition: all 0.2s;
                }
                .main-panel.light-theme .overview-quick-btn {
                    background: #e2e8f0;
                    color: #334155;
                }
                .main-panel.dark-theme .overview-quick-btn {
                    background: rgba(255,255,255,0.06);
                    color: #cbd5e1;
                }
                .overview-quick-btn:hover {
                    background: var(--primary);
                    color: white;
                }
                
                .main-panel.light-theme .overview-stat-card {
                    background: #f8fafc;
                    border: 1px solid #e2e8f0;
                }
                .main-panel.dark-theme .overview-stat-card {
                    background: rgba(30, 41, 59, 0.3);
                    border: 1px solid rgba(255, 255, 255, 0.05);
                }
            </style>
            
            <h3 style="text-align:center; font-family:'Outfit', sans-serif; font-size:1.8rem; font-weight:800; margin-bottom:10px;">📈 策略進出場成績總覽 (V8.1)</h3>
            <p style="text-align:center; color:var(--text-muted); font-size:0.95rem; margin-bottom:25px;">查看並篩選精選策略，動態模擬投資組合進出場成績、投入成本與投報率。</p>
            
            <div class="control-panel" style="margin-bottom: 25px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 15px; padding: 15px; background: rgba(0,0,0,0.15); border-radius: 10px; border: 1px solid var(--border);">
                <div style="display: flex; align-items: center; gap: 15px; flex-wrap: wrap;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span>📅 開始日期：</span>
                        <input type="date" id="overview_start_date" value="2026-01-01" onchange="updateStrategyOverviewUI()" style="padding: 6px 12px; border-radius: 6px; border: 1px solid var(--border); background: rgba(0,0,0,0.2); color: inherit; font-weight: 600;">
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span>📅 結束日期：</span>
                        <input type="date" id="overview_end_date" onchange="updateStrategyOverviewUI()" style="padding: 6px 12px; border-radius: 6px; border: 1px solid var(--border); background: rgba(0,0,0,0.2); color: inherit; font-weight: 600;">
                    </div>
                </div>
                <div style="font-weight: 700; font-size: 0.95rem; color: var(--primary); display: flex; align-items: center; gap: 6px;">
                    <span>目前篩選：</span>
                    <span id="overview_direction_badge" style="background: rgba(99, 102, 241, 0.15); padding: 4px 10px; border-radius: 20px; font-size: 0.85rem;">📈 多單策略</span>
                </div>
            </div>

            <div class="overview-container">
                <!-- 左側：個股選取側邊欄 -->
                <div class="overview-sidebar">
                    <h4 style="font-size:0.95rem; font-weight:700; border-bottom: 1px solid var(--border); padding-bottom:8px;">🎯 選取個股</h4>
                    <input type="text" id="overview_stock_search" placeholder="🔍 搜尋個股..." class="overview-search-box" oninput="filterOverviewStockList()">
                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px; margin-top:5px;">
                        <button class="overview-quick-btn" onclick="selectOverviewStocks('all')">全選</button>
                        <button class="overview-quick-btn" onclick="selectOverviewStocks('none')">全不選</button>
                    </div>
                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px; margin-bottom:5px;">
                        <button class="overview-quick-btn" onclick="selectOverviewStocks('top5')">勝率前 5</button>
                        <button class="overview-quick-btn" onclick="selectOverviewStocks('top10')">勝率前 10</button>
                    </div>
                    <div id="overview_stock_list_container" style="display:flex; flex-direction:column; gap:8px;">
                        <!-- 個股複選框動態生成 -->
                    </div>
                </div>

                <!-- 右側：數據統計與表格 -->
                <div class="overview-main">
                    <div class="overview-stats-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                        <div class="overview-stat-card" style="padding: 20px; border-radius: 12px; text-align: center;">
                            <div style="color: var(--text-muted); font-size: 0.82rem; font-weight: 600; text-transform: uppercase; margin-bottom: 8px;">預估總投入成本</div>
                            <div id="overview_stat_cost" style="font-size: 1.5rem; font-weight: 800; color: var(--text-main);">$0</div>
                        </div>
                        <div class="overview-stat-card" style="padding: 20px; border-radius: 12px; text-align: center;">
                            <div style="color: var(--text-muted); font-size: 0.82rem; font-weight: 600; text-transform: uppercase; margin-bottom: 8px;">投資組合累積淨損益</div>
                            <div id="overview_stat_profit" style="font-size: 1.5rem; font-weight: 800; color: var(--text-main);">$0</div>
                        </div>
                        <div class="overview-stat-card" style="padding: 20px; border-radius: 12px; text-align: center;">
                            <div style="color: var(--text-muted); font-size: 0.82rem; font-weight: 600; text-transform: uppercase; margin-bottom: 8px;">投資組合投報率 (ROI)</div>
                            <div id="overview_stat_roi" style="font-size: 1.5rem; font-weight: 800; color: var(--text-main);">0.00%</div>
                        </div>
                        <div class="overview-stat-card" style="padding: 20px; border-radius: 12px; text-align: center;">
                            <div style="color: var(--text-muted); font-size: 0.82rem; font-weight: 600; text-transform: uppercase; margin-bottom: 8px;">交易統計 & 勝率</div>
                            <div id="overview_stat_winrate_trades" style="font-size: 1.5rem; font-weight: 800; color: var(--text-main);">0% (0次)</div>
                        </div>
                    </div>

                    <div class="collapsible-section" style="margin-bottom: 10px;">
                        <div class="collapsible-header" style="background: rgba(99, 102, 241, 0.1); color: var(--text-main); cursor: pointer;" onclick="this.parentElement.classList.toggle('collapsed')">
                            <span>📊 目前有持倉的個股 (未實現損益模擬)</span>
                            <span class="collapse-icon">▼</span>
                        </div>
                        <div class="collapsible-content" style="padding: 15px;">
                            <table class="info-table" id="overview_holdings_table">
                                <thead>
                                    <tr style="background:rgba(0,0,0,0.1);">
                                        <th style="padding:10px; font-weight:700;">個股代號/名稱</th>
                                        <th style="padding:10px; font-weight:700;">持倉類型</th>
                                        <th style="padding:10px; font-weight:700;">進場日期</th>
                                        <th style="padding:10px; font-weight:700;">進場價格</th>
                                        <th style="padding:10px; font-weight:700;">目前價格</th>
                                        <th style="padding:10px; font-weight:700;">模擬持倉損益</th>
                                        <th style="padding:10px; font-weight:700;">模擬持倉 ROI</th>
                                        <th style="padding:10px; font-weight:700;">操作</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <!-- 動態插入持倉列 -->
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <div class="collapsible-section">
                        <div class="collapsible-header" style="background: rgba(99, 102, 241, 0.1); color: var(--text-main); cursor: pointer;" onclick="this.parentElement.classList.toggle('collapsed')">
                            <span>📂 已完成交易歷史明細</span>
                            <span class="collapse-icon">▼</span>
                        </div>
                        <div class="collapsible-content" style="padding: 0;">
                            <table class="info-table" id="overview_history_table">
                                <thead>
                                    <tr style="background:rgba(0,0,0,0.1);">
                                        <th style="padding:12px; font-weight:700;">個股代號/名稱</th>
                                        <th style="padding:12px; font-weight:700;">類型</th>
                                        <th style="padding:12px; font-weight:700;">策略組合</th>
                                        <th style="padding:12px; font-weight:700;">進場日期</th>
                                        <th style="padding:12px; font-weight:700;">進場價格</th>
                                        <th style="padding:12px; font-weight:700;">出場日期</th>
                                        <th style="padding:12px; font-weight:700;">出場價格</th>
                                        <th style="padding:12px; font-weight:700;">交易損益</th>
                                        <th style="padding:12px; font-weight:700;">投報率 (ROI)</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <!-- 動態插入歷史交易 -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>"""
NEW_LOAD_LEADERBOARD_CONTENT = """        async function loadLeaderboardData() {
            try {
                backtestRegistry = {};
                activeHoldings = {};
                
                const res = await fetch('/leaderboard_v8.json');
                if (res.ok) {
                    const data = await res.json();
                    data.forEach(item => {
                        const uniqueId = `s${item.code}_ai`;
                        backtestRegistry[uniqueId] = {
                            code: item.code,
                            name: item.name,
                            profit: item.profit,
                            roi: item.roi,
                            winRate: item.winRate,
                            trades: item.trades,
                            strategy: item.strategy,
                            type: item.type || 'long'
                        };
                        
                        if (item.holding) {
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
                        }
                    });
                }
                
                const resTrades = await fetch('/trades_v8.json');
                if (resTrades.ok) {
                    allTradesHistory = await resTrades.json();
                }
                
                updatePerformanceLeaderboard();
                
                // V8.1: 初始化複選名單與預設勾選
                const directionStocks = Object.values(backtestRegistry).filter(s => s.type === activeDirection);
                selectedOverviewStocks = directionStocks.map(s => s.code);
                renderOverviewStockList();
                updateStrategyOverviewUI();
            } catch (err) {
                console.error("loadLeaderboardData error:", err);
            }
        }"""
NEW_JS_FUNCTIONS = """        // V8 交易方向與成績總覽邏輯 (V8.1 升級版)
        let selectedOverviewStocks = []; // Array of stock codes selected for simulation
        
        function renderOverviewStockList() {
            const container = document.getElementById('overview_stock_list_container');
            if (!container) return;
            container.innerHTML = '';
            
            // Get all stocks from backtestRegistry matching activeDirection
            let stocks = Object.values(backtestRegistry).filter(s => s.type === activeDirection);
            
            // Apply search filter if any
            const searchInput = document.getElementById('overview_stock_search');
            const searchVal = searchInput ? searchInput.value.trim().toLowerCase() : '';
            if (searchVal) {
                stocks = stocks.filter(s => s.code.includes(searchVal) || s.name.toLowerCase().includes(searchVal));
            }
            
            // Sort by winRate descending
            stocks.sort((a, b) => b.winRate - a.winRate);
            
            if (stocks.length === 0) {
                container.innerHTML = `<div style="text-align:center; color:var(--text-muted); font-size:0.85rem; padding:15px;">無符合條件的個股</div>`;
                return;
            }
            
            stocks.forEach(s => {
                const isChecked = selectedOverviewStocks.includes(s.code);
                const itemDiv = document.createElement('div');
                itemDiv.className = 'overview-stock-item';
                itemDiv.onclick = (e) => {
                    if (e.target.tagName === 'INPUT') return;
                    const chk = itemDiv.querySelector('input[type="checkbox"]');
                    chk.checked = !chk.checked;
                    toggleStockSelection(s.code, chk.checked);
                };
                
                itemDiv.innerHTML = `
                    <input type="checkbox" data-code="${s.code}" ${isChecked ? 'checked' : ''} onchange="toggleStockSelection('${s.code}', this.checked)">
                    <div style="flex:1; display:flex; justify-content:space-between; align-items:center; font-size:0.9rem;">
                        <span style="font-weight:600;">\${s.code} \${s.name}</span>
                        <span style="color:#10b981; font-weight:700; font-size:0.8rem;">\${s.winRate.toFixed(1)}%勝率</span>
                    </div>
                `;
                container.appendChild(itemDiv);
            });
        }
        
        function toggleStockSelection(code, checked) {
            if (checked) {
                if (!selectedOverviewStocks.includes(code)) {
                    selectedOverviewStocks.push(code);
                }
            } else {
                selectedOverviewStocks = selectedOverviewStocks.filter(c => c !== code);
            }
            updateStrategyOverviewUI();
        }
        
        function selectOverviewStocks(mode) {
            let stocks = Object.values(backtestRegistry).filter(s => s.type === activeDirection);
            
            if (mode === 'all') {
                selectedOverviewStocks = stocks.map(s => s.code);
            } else if (mode === 'none') {
                selectedOverviewStocks = [];
            } else if (mode === 'top5') {
                const sorted = [...stocks].sort((a, b) => b.winRate - a.winRate);
                selectedOverviewStocks = sorted.slice(0, 5).map(s => s.code);
            } else if (mode === 'top10') {
                const sorted = [...stocks].sort((a, b) => b.winRate - a.winRate);
                selectedOverviewStocks = sorted.slice(0, 10).map(s => s.code);
            }
            
            renderOverviewStockList();
            updateStrategyOverviewUI();
        }
        
        function filterOverviewStockList() {
            renderOverviewStockList();
        }

        function changeActiveDirection(dir) {
            if (activeDirection === dir) return;
            activeDirection = dir;
            
            const btnLong = document.getElementById('toggle_pos_long');
            const btnShort = document.getElementById('toggle_pos_short');
            if (btnLong && btnShort) {
                if (dir === 'long') {
                    btnLong.style.background = 'var(--primary)';
                    btnLong.style.color = 'white';
                    btnShort.style.background = 'transparent';
                    btnShort.style.color = 'var(--text-muted)';
                } else {
                    btnLong.style.background = 'transparent';
                    btnLong.style.color = 'var(--text-muted)';
                    btnShort.style.background = 'var(--primary)';
                    btnShort.style.color = 'white';
                }
            }
            
            renderSidebarStocks();
            
            // V8.1: 切換交易方向時預設勾選全部個股
            const directionStocks = Object.values(backtestRegistry).filter(s => s.type === dir);
            selectedOverviewStocks = directionStocks.map(s => s.code);
            
            if (activeTabId === 'performance') {
                updatePerformanceLeaderboard();
            } else if (activeTabId === 'overview') {
                renderOverviewStockList();
                updateStrategyOverviewUI();
            } else {
                selectPerformanceTab();
            }
        }

        function selectOverviewTab() {
            closeSidebarOnMobile();
            activeTabId = 'overview';
            document.querySelectorAll('.stock-item').forEach(i => i.classList.remove('active'));
            document.querySelectorAll('.strategy-folder').forEach(f => f.classList.remove('active-folder'));
            const fold = document.getElementById('folder_overview');
            if (fold) fold.classList.add('active-folder');

            document.querySelectorAll('#main_panel .page').forEach(p => p.classList.remove('active'));
            const tabOver = document.getElementById('tab_overview');
            if (tabOver) tabOver.classList.add('active');

            renderOverviewStockList();
            updateStrategyOverviewUI();
        }

        function updateStrategyOverviewUI() {
            const badge = document.getElementById('overview_direction_badge');
            if (badge) {
                badge.textContent = activeDirection === 'long' ? '📈 多單策略' : '📉 空單策略';
                badge.style.background = activeDirection === 'long' ? 'rgba(99, 102, 241, 0.15)' : 'rgba(168, 85, 247, 0.15)';
                badge.style.color = activeDirection === 'long' ? '#4f46e5' : '#a855f7';
            }

            const startInput = document.getElementById('overview_start_date');
            const endInput = document.getElementById('overview_end_date');
            if (!startInput || !endInput) return;

            const startDateStr = startInput.value.replace(/-/g, '');
            const endDateStr = endInput.value.replace(/-/g, '');

            if (!startDateStr || !endDateStr) return;

            // 1. 篩選已完成交易 (限已選取個股)
            const filteredTrades = allTradesHistory.filter(t => {
                const isDirMatch = t.type === activeDirection;
                if (!isDirMatch) return false;
                if (!selectedOverviewStocks.includes(t.code)) return false;
                const exitDate = String(t.exitDate || '').replace(/-/g, '');
                return exitDate >= startDateStr && exitDate <= endDateStr;
            });

            // 2. 篩選未實現持倉 (限已選取個股)
            const filteredHoldings = Object.values(activeHoldings).filter(h => {
                const hType = h.type || (h.posType === '空單' ? 'short' : 'long');
                if (hType !== activeDirection) return false;
                if (!selectedOverviewStocks.includes(h.code)) return false;
                const buyDateStr = String(h.buyDate || '').replace(/-/g, '');
                return buyDateStr <= endDateStr;
            });

            // 3. 計算投資組合累計損益與勝率
            let totalProfit = 0;
            let winningTrades = 0;
            const totalTrades = filteredTrades.length;

            filteredTrades.forEach(t => {
                totalProfit += (t.pnl || 0);
                if ((t.pnl || 0) > 0) winningTrades++;
            });

            filteredHoldings.forEach(h => {
                totalProfit += (h.pnl || 0);
            });

            // 4. 計算投資組合所需總成本 (每檔勾選個股於期間內的最大進場價 * 1000)
            let totalCost = 0;
            selectedOverviewStocks.forEach(code => {
                let entryPrices = [];
                
                filteredTrades.forEach(t => {
                    if (t.code === code && t.entryPrice) {
                        entryPrices.push(t.entryPrice);
                    }
                });
                
                filteredHoldings.forEach(h => {
                    if (h.code === code && h.buyPrice) {
                        entryPrices.push(h.buyPrice);
                    }
                });
                
                if (entryPrices.length > 0) {
                    const maxPrice = Math.max(...entryPrices);
                    totalCost += maxPrice * 1000;
                }
            });

            const portfolioRoi = totalCost > 0 ? (totalProfit / totalCost * 100) : 0;
            const winRate = totalTrades > 0 ? (winningTrades / totalTrades * 100) : 0;

            // 更新數據卡片 UI
            const costEl = document.getElementById('overview_stat_cost');
            if (costEl) costEl.textContent = totalCost.toLocaleString() + ' 元';
            
            const profitEl = document.getElementById('overview_stat_profit');
            if (profitEl) {
                profitEl.textContent = (totalProfit >= 0 ? '+' : '') + totalProfit.toLocaleString() + ' 元';
                profitEl.style.color = totalProfit >= 0 ? '#10b981' : '#ef4444';
            }
            
            const roiEl = document.getElementById('overview_stat_roi');
            if (roiEl) {
                roiEl.textContent = (portfolioRoi >= 0 ? '+' : '') + portfolioRoi.toFixed(2) + '%';
                roiEl.style.color = portfolioRoi >= 0 ? '#10b981' : '#ef4444';
            }
            
            const winrateTradesEl = document.getElementById('overview_stat_winrate_trades');
            if (winrateTradesEl) {
                winrateTradesEl.textContent = winRate.toFixed(1) + '% (' + totalTrades + '次)';
            }

            // 渲染持倉表格
            const holdingsBody = document.querySelector('#overview_holdings_table tbody');
            if (holdingsBody) {
                holdingsBody.innerHTML = '';
                if (filteredHoldings.length === 0) {
                    holdingsBody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:15px; color:var(--text-muted);">📭 目前所選個股無持倉部位</td></tr>`;
                } else {
                    filteredHoldings.forEach(h => {
                        const tr = document.createElement('tr');
                        const pnlColor = h.pnl >= 0 ? '#10b981' : '#ef4444';
                        tr.innerHTML = `
                            <td style="padding:10px; font-weight:600;">\${h.code} \${h.name}</td>
                            <td style="padding:10px;"><span style="background:\${h.posType === '空單' ? 'rgba(168, 85, 247, 0.15)' : 'rgba(99, 102, 241, 0.15)'}; color:\${h.posType === '空單' ? '#a855f7' : '#4f46e5'}; padding:2px 8px; border-radius:12px; font-size:0.8rem; font-weight:700;">\${h.posType}</span></td>
                            <td style="padding:10px;">\${h.buyDate}</td>
                            <td style="padding:10px;">\${(h.buyPrice || 0).toFixed(2)}</td>
                            <td style="padding:10px;">\${(h.currentPrice || 0).toFixed(2)}</td>
                            <td style="padding:10px; font-weight:700; color:\${pnlColor};">\${(h.pnl >= 0 ? '+' : '') + h.pnl.toLocaleString()}</td>
                            <td style="padding:10px; font-weight:700; color:\${pnlColor};">\${(h.roi >= 0 ? '+' : '') + h.roi.toFixed(2)}%</td>
                            <td style="padding:10px;"><button onclick="const stk = preloadedStocks.find(s => s.id === '\${h.uniqueId}'); selectStockTab('\${h.uniqueId}', '\${h.code}', '\${h.name}', stk ? stk.strategy : 'ai_trend', 'preload')" style="padding:4px 8px; background:#4f46e5; color:white; border:none; border-radius:4px; font-size:0.8rem; cursor:pointer;">🔍 查看</button></td>
                        `;
                        holdingsBody.appendChild(tr);
                    });
                }
            }

            // 渲染交易歷史表格
            const historyBody = document.querySelector('#overview_history_table tbody');
            if (historyBody) {
                historyBody.innerHTML = '';
                if (filteredTrades.length === 0) {
                    historyBody.innerHTML = `<tr><td colspan="9" style="text-align:center; padding:30px; color:var(--text-muted);">📭 選擇的日期與個股範圍內無交易記錄</td></tr>`;
                } else {
                    const displayList = [...filteredTrades].sort((a,b) => String(b.exitDate).localeCompare(String(a.exitDate)));
                    displayList.forEach(t => {
                        const tr = document.createElement('tr');
                        const pnlColor = t.pnl >= 0 ? '#10b981' : '#ef4444';
                        tr.innerHTML = `
                            <td style="padding:12px; font-weight:600;">\${t.code} \${t.name}</td>
                            <td style="padding:12px;"><span style="background:\${t.posType === '空單' ? 'rgba(168, 85, 247, 0.15)' : 'rgba(99, 102, 241, 0.15)'}; color:\${t.posType === '空單' ? '#a855f7' : '#4f46e5'}; padding:2px 8px; border-radius:12px; font-size:0.8rem; font-weight:700;">\${t.posType}</span></td>
                            <td style="padding:12px; font-size:0.85rem; color:var(--text-muted);">\${t.strategy}</td>
                            <td style="padding:12px;">\${t.entryDate}</td>
                            <td style="padding:12px;">\${(t.entryPrice || 0).toFixed(2)}</td>
                            <td style="padding:12px;">\${t.exitDate}</td>
                            <td style="padding:12px;">\${(t.exitPrice || 0).toFixed(2)}</td>
                            <td style="padding:12px; font-weight:700; color:\${pnlColor};">\${(t.pnl >= 0 ? '+' : '') + t.pnl.toLocaleString()}</td>
                            <td style="padding:12px; font-weight:700; color:\${pnlColor};">\${(t.roi >= 0 ? '+' : '') + t.roi.toFixed(2)}%</td>
                        `;
                        historyBody.appendChild(tr);
                    });
                }
            }
        }"""
# -*- coding: utf-8 -*-
import os

HTML_PATH = r"E:\G-AI-1\Stock analysis\修正版_V6_Server\public\dashboard_v8_1_backup.html"

def main():
    print("=" * 60)
    print("  V8 前端邏輯自動注入/修改腳本...")
    print("=" * 60)

    if not os.path.exists(HTML_PATH):
        print(f"[錯誤] {HTML_PATH} 不存在！")
        return

    with open(HTML_PATH, 'r', encoding='utf-8') as f:
        html = f.read()

    # ── 1. 注入 V8 全局變數 ──
    old_state = "        let activeHoldings = {};"
    new_state = """        let activeHoldings = {};
        let activeDirection = 'long'; // V8: 'long' or 'short'
        let allTradesHistory = [];    // V8: 儲存所有完成的交易歷史"""
    if old_state in html and "activeDirection" not in html:
        html = html.replace(old_state, new_state)
        print("  [成功] 注入 V8 全局狀態變數")

    # ── 2. 注入多單/空單側邊欄切換按鈕 ──
    old_sidebar_menu = '        <!-- 側邊欄菜單 -->'
    new_sidebar_menu = """        <!-- 交易方向切換 (V8) -->
        <div style="padding: 10px 15px; border-bottom: 1px solid var(--border); display: flex; flex-direction: column; gap: 8px;">
            <label style="font-size: 0.75rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px;">策略交易方向</label>
            <div style="display: grid; grid-template-columns: 1fr 1fr; background: rgba(0,0,0,0.2); border-radius: 8px; padding: 3px; border: 1px solid var(--border);">
                <button id="toggle_pos_long" onclick="changeActiveDirection('long')" style="padding: 8px; border: none; border-radius: 6px; font-size: 0.85rem; font-weight: bold; cursor: pointer; transition: all 0.2s; background: var(--primary); color: white;">📈 多單策略</button>
                <button id="toggle_pos_short" onclick="changeActiveDirection('short')" style="padding: 8px; border: none; border-radius: 6px; font-size: 0.85rem; font-weight: bold; cursor: pointer; transition: all 0.2s; background: transparent; color: var(--text-muted);">📉 空單策略</button>
            </div>
        </div>

        <!-- 側邊欄菜單 -->"""
    if old_sidebar_menu in html and "toggle_pos_long" not in html:
        html = html.replace(old_sidebar_menu, new_sidebar_menu)
        print("  [成功] 注入側邊欄交易方向切換按鈕")

    # ── 3. 注入「策略進出場成績總覽」側邊欄入口 ──
    old_perf_folder = """            <!-- 績效排行榜 (New Performance Area Folder) -->
            <div class="strategy-folder active-folder" id="folder_performance" style="margin-bottom: 15px;">
                <div class="folder-header" onclick="selectPerformanceTab()" style="background: rgba(99, 102, 241, 0.15); border-color: rgba(99, 102, 241, 0.4);">
                    <div class="folder-title" style="color: #818cf8;">
                        <span>🏆 策略績效排行榜</span>
                    </div>
                </div>
            </div>"""
    new_perf_folder = """            <!-- 績效排行榜 (New Performance Area Folder) -->
            <div class="strategy-folder active-folder" id="folder_performance" style="margin-bottom: 15px;">
                <div class="folder-header" onclick="selectPerformanceTab()" style="background: rgba(99, 102, 241, 0.15); border-color: rgba(99, 102, 241, 0.4);">
                    <div class="folder-title" style="color: #818cf8;">
                        <span>🏆 策略績效排行榜</span>
                    </div>
                </div>
            </div>

            <!-- 策略進出場成績總覽 (V8) -->
            <div class="strategy-folder" id="folder_overview" style="margin-bottom: 15px;">
                <div class="folder-header" onclick="selectOverviewTab()" style="background: rgba(168, 85, 247, 0.15); border-color: rgba(168, 85, 247, 0.4); cursor: pointer;">
                    <div class="folder-title" style="color: #c084fc;">
                        <span>📈 策略進出場成績總覽</span>
                    </div>
                </div>
            </div>"""
    if old_perf_folder in html and "folder_overview" not in html:
        html = html.replace(old_perf_folder, new_perf_folder)
        print("  [成功] 注入成績總覽側邊欄入口")

    # ── 4. 注入「策略進出場成績總覽」主顯示面板 ──
    old_holding_summary = '        <!-- 📊 持倉總覽面板 -->'
    new_holding_summary = NEW_HTML_CONTENT
    _dummy_html = """
        <div id="tab_overview" class="page" style="max-width: 1280px; margin: 0 auto; background: white; padding: 30px; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); display: none;">
            <h3 style="text-align:center; font-family:'Outfit', sans-serif; font-size:1.8rem; font-weight:800; margin-bottom:10px;">📈 策略進出場成績總覽</h3>
            <p style="text-align:center; color:#64748b; font-size:0.95rem; margin-bottom:25px;">查看精選策略在自訂區間內的進出場總體績效成績與當前持倉個股。</p>
            
            <div class="control-panel" style="margin-bottom: 25px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 15px; padding: 15px; background: #f8fafc; border-radius: 10px; border: 1px solid #e2e8f0;">
                <div style="display: flex; align-items: center; gap: 15px; flex-wrap: wrap;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span>📅 開始日期：</span>
                        <input type="date" id="overview_start_date" value="2026-01-01" onchange="updateStrategyOverviewUI()" style="padding: 6px 12px; border-radius: 6px; border: 1px solid #cbd5e1; font-weight: 600;">
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span>📅 結束日期：</span>
                        <input type="date" id="overview_end_date" onchange="updateStrategyOverviewUI()" style="padding: 6px 12px; border-radius: 6px; border: 1px solid #cbd5e1; font-weight: 600;">
                    </div>
                </div>
                <div style="font-weight: 700; font-size: 0.95rem; color: #4f46e5; display: flex; align-items: center; gap: 6px;">
                    <span>目前篩選：</span>
                    <span id="overview_direction_badge" style="background: rgba(99, 102, 241, 0.15); padding: 4px 10px; border-radius: 20px; font-size: 0.85rem;">📈 多單策略</span>
                </div>
            </div>

            <div class="overview-stats-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; margin-bottom: 30px;">
                <div style="background: #f8fafc; border: 1px solid #e2e8f0; padding: 20px; border-radius: 12px; text-align: center;">
                    <div style="color: #64748b; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; margin-bottom: 8px;">累積淨損益</div>
                    <div id="overview_stat_profit" style="font-size: 1.8rem; font-weight: 800; color: #0f172a;">$0</div>
                </div>
                <div style="background: #f8fafc; border: 1px solid #e2e8f0; padding: 20px; border-radius: 12px; text-align: center;">
                    <div style="color: #64748b; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; margin-bottom: 8px;">交易勝率</div>
                    <div id="overview_stat_winrate" style="font-size: 1.8rem; font-weight: 800; color: #0f172a;">0%</div>
                </div>
                <div style="background: #f8fafc; border: 1px solid #e2e8f0; padding: 20px; border-radius: 12px; text-align: center;">
                    <div style="color: #64748b; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; margin-bottom: 8px;">總交易次數</div>
                    <div id="overview_stat_trades" style="font-size: 1.8rem; font-weight: 800; color: #0f172a;">0</div>
                </div>
                <div style="background: #f8fafc; border: 1px solid #e2e8f0; padding: 20px; border-radius: 12px; text-align: center;">
                    <div style="color: #64748b; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; margin-bottom: 8px;">平均單筆投報率</div>
                    <div id="overview_stat_avgroi" style="font-size: 1.8rem; font-weight: 800; color: #0f172a;">0%</div>
                </div>
            </div>

            <div class="collapsible-section" style="margin-bottom: 30px;">
                <div class="collapsible-header" style="background: #f1f5f9; color: #1e293b;">
                    <span>📊 目前有持倉的個股 (未實現損益模擬)</span>
                </div>
                <div class="collapsible-content" style="padding: 15px;">
                    <table class="info-table" id="overview_holdings_table">
                        <thead>
                            <tr style="background:#f8fafc;">
                                <th style="padding:10px; font-weight:700;">個股代號/名稱</th>
                                <th style="padding:10px; font-weight:700;">持倉類型</th>
                                <th style="padding:10px; font-weight:700;">進場日期</th>
                                <th style="padding:10px; font-weight:700;">進場價格</th>
                                <th style="padding:10px; font-weight:700;">目前價格</th>
                                <th style="padding:10px; font-weight:700;">模擬持倉損益</th>
                                <th style="padding:10px; font-weight:700;">模擬持倉 ROI</th>
                                <th style="padding:10px; font-weight:700;">操作</th>
                            </tr>
                        </thead>
                        <tbody>
                            <!-- 動態插入持倉列 -->
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="collapsible-section">
                <div class="collapsible-header" style="background: #f1f5f9; color: #1e293b;">
                    <span>📂 已完成交易歷史明細</span>
                </div>
                <div class="collapsible-content" style="padding: 0;">
                    <table class="info-table" id="overview_history_table">
                        <thead>
                            <tr style="background:#f1f5f9;">
                                <th style="padding:12px; font-weight:700;">個股代號/名稱</th>
                                <th style="padding:12px; font-weight:700;">類型</th>
                                <th style="padding:12px; font-weight:700;">策略組合</th>
                                <th style="padding:12px; font-weight:700;">進場日期</th>
                                <th style="padding:12px; font-weight:700;">進場價格</th>
                                <th style="padding:12px; font-weight:700;">出場日期</th>
                                <th style="padding:12px; font-weight:700;">出場價格</th>
                                <th style="padding:12px; font-weight:700;">交易損益</th>
                                <th style="padding:12px; font-weight:700;">投報率 (ROI)</th>
                            </tr>
                        </thead>
                        <tbody>
                            <!-- 動態插入歷史交易 -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- 📊 持倉總覽面板 -->"""
    if "<!-- 📈 策略進出場成績總覽頁面" in html:
        start_idx = html.find("<!-- 📈 策略進出場成績總覽頁面")
        end_idx = html.find("<!-- 📊 持倉總覽面板 -->")
        if start_idx != -1 and end_idx != -1:
            old_block = html[start_idx:end_idx]
            html = html.replace(old_block, new_holding_summary)
            print("  [成功] 升級策略進出場成績總覽主面板 HTML (V8 -> V8.1)")
    else:
        if old_holding_summary in html:
            html = html.replace(old_holding_summary, new_holding_summary + old_holding_summary)
            print("  [成功] 注入策略進出場成績總覽主面板 HTML")

    # ── 5. 修改 `loadLeaderboardData` 載入 V8 排行榜與交易記錄 ──
    old_load_leaderboard = """        async function loadLeaderboardData() {
            try {
                const res = await fetch('/leaderboard.json');
                if (res.ok) {
                    const data = await res.json();
                    data.forEach(item => {
                        const uniqueId = `s${item.code}_ai`;
                        backtestRegistry[uniqueId] = {
                            code: item.code,
                            name: item.name,
                            profit: item.profit,
                            roi: item.roi,
                            winRate: item.winRate,
                            trades: item.trades,
                            strategy: item.strategy
                        };
                        
                        // 注入來自後端的持倉資訊 (V7 改進版)
                        if (item.holding) {
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
                                posType: item.holding.posType || '多單'
                            };
                        }
                    });
                }
                updatePerformanceLeaderboard();
            } catch (err) {
                console.error("loadLeaderboardData error:", err);
            }
        }"""

    new_load_leaderboard = NEW_LOAD_LEADERBOARD_CONTENT
    _dummy_load = """
            try {
                backtestRegistry = {};
                activeHoldings = {};
                
                const res = await fetch('/leaderboard_v8.json');
                if (res.ok) {
                    const data = await res.json();
                    data.forEach(item => {
                        const uniqueId = `s${item.code}_ai`;
                        backtestRegistry[uniqueId] = {
                            code: item.code,
                            name: item.name,
                            profit: item.profit,
                            roi: item.roi,
                            winRate: item.winRate,
                            trades: item.trades,
                            strategy: item.strategy,
                            type: item.type || 'long'
                        };
                        
                        if (item.holding) {
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
                        }
                    });
                }
                
                const resTrades = await fetch('/trades_v8.json');
                if (resTrades.ok) {
                    allTradesHistory = await resTrades.json();
                }
                
                updatePerformanceLeaderboard();
                updateStrategyOverviewUI();
            } catch (err) {
                console.error("loadLeaderboardData error:", err);
            }
        }"""
    if "async function loadLeaderboardData()" in html:
        start_load_idx = html.find("async function loadLeaderboardData()")
        end_load_idx = html.find("無法加載靜態排行榜數據:")
        if end_load_idx == -1:
            end_load_idx = html.find("loadLeaderboardData error:")
        
        if start_load_idx != -1 and end_load_idx != -1:
            closing_idx = html.find("}", end_load_idx)
            closing_idx = html.find("}", closing_idx + 1)
            if closing_idx != -1:
                old_load_block = html[start_load_idx:closing_idx + 1]
                html = html.replace(old_load_block, new_load_leaderboard.strip())
                print("  [成功] 升級 loadLeaderboardData (V8 -> V8.1)")

    # ── 6. 修改 `updatePerformanceLeaderboard` 過濾 activeDirection ──
    old_data_list = """            let dataList = Object.entries(backtestRegistry).map(([uniqueId, data]) => ({
                uniqueId,
                ...data
            }));"""
    new_data_list = """            let dataList = Object.entries(backtestRegistry).map(([uniqueId, data]) => ({
                uniqueId,
                ...data
            }));
            
            // V8: 過濾交易方向
            dataList = dataList.filter(item => (item.type || 'long') === activeDirection);"""
    if old_data_list in html and "V8: 過濾交易方向" not in html:
        html = html.replace(old_data_list, new_data_list)
        print("  [成功] 修改 updatePerformanceLeaderboard 支援方向篩選")

    # ── 7. 修改 `renderSidebarStocks` 過濾與隱藏無效策略 ──
    old_render_sidebar = """        function renderSidebarStocks() {
            document.getElementById('contents_v4').innerHTML = '';
            document.getElementById('contents_rebound').innerHTML = '';
            document.getElementById('contents_dipbuy').innerHTML = '';
            document.getElementById('contents_v38').innerHTML = '';
            ['ai_trend', 'ai_rebound', 'ai_oversold', 'ai_support'].forEach(f => {
                const el = document.getElementById('contents_' + f);
                if (el) el.innerHTML = '';
            });

            // 1. 系統內建個股
            preloadedStocks.forEach(stock => {
                appendStockToSidebar(stock.id, stock.name, stock.strategy, 'preload');
            });

            // 2. 自訂上傳個股
            userCustomStocks.forEach(stock => {
                appendStockToSidebar(stock.code, stock.name, stock.strategy, 'custom', stock.uniqueId);
            });
        }"""
    
    new_render_sidebar = """        function renderSidebarStocks() {
            document.getElementById('contents_v4').innerHTML = '';
            document.getElementById('contents_rebound').innerHTML = '';
            document.getElementById('contents_dipbuy').innerHTML = '';
            document.getElementById('contents_v38').innerHTML = '';
            ['ai_trend', 'ai_rebound', 'ai_oversold', 'ai_support'].forEach(f => {
                const el = document.getElementById('contents_' + f);
                if (el) el.innerHTML = '';
            });

            // 1. 系統內建個股 (V8 過濾交易方向)
            preloadedStocks.forEach(stock => {
                const stockType = stock.type || 'long';
                if (stockType === activeDirection) {
                    appendStockToSidebar(stock.id, stock.name, stock.strategy, 'preload');
                }
            });

            // 2. 自訂上傳個股
            userCustomStocks.forEach(stock => {
                const stockType = stock.type || 'long';
                if (stockType === activeDirection) {
                    appendStockToSidebar(stock.code, stock.name, stock.strategy, 'custom', stock.uniqueId);
                }
            });
            
            // V8: 同時隱藏/顯示非 active 策略的 folder (空單時隱藏內建的 V4, Rebound 等做多策略)
            const isShort = activeDirection === 'short';
            const fV4 = document.getElementById('folder_v4');
            const fReb = document.getElementById('folder_rebound');
            const fDip = document.getElementById('folder_dipbuy');
            const fV38 = document.getElementById('folder_v38');
            if (fV4) fV4.style.display = isShort ? 'none' : 'block';
            if (fReb) fReb.style.display = isShort ? 'none' : 'block';
            if (fDip) fDip.style.display = isShort ? 'none' : 'block';
            if (fV38) fV38.style.display = isShort ? 'none' : 'block';
        }"""
    if old_render_sidebar in html:
        html = html.replace(old_render_sidebar, new_render_sidebar)
        print("  [成功] 修改 renderSidebarStocks 支援 V8 方向過濾與隱藏")

    # ── 8. 注入 V8 各種控制與更新函數 (放置於隨意一處 JS 區間)
    marker_function = "        // 切換至績效排行榜"
    new_v8_functions = NEW_JS_FUNCTIONS
    _dummy_fns = """
        function changeActiveDirection(dir) {
            if (activeDirection === dir) return;
            activeDirection = dir;
            
            const btnLong = document.getElementById('toggle_pos_long');
            const btnShort = document.getElementById('toggle_pos_short');
            if (btnLong && btnShort) {
                if (dir === 'long') {
                    btnLong.style.background = 'var(--primary)';
                    btnLong.style.color = 'white';
                    btnShort.style.background = 'transparent';
                    btnShort.style.color = 'var(--text-muted)';
                } else {
                    btnLong.style.background = 'transparent';
                    btnLong.style.color = 'var(--text-muted)';
                    btnShort.style.background = 'var(--primary)';
                    btnShort.style.color = 'white';
                }
            }
            
            renderSidebarStocks();
            
            if (activeTabId === 'performance') {
                updatePerformanceLeaderboard();
            } else if (activeTabId === 'overview') {
                updateStrategyOverviewUI();
            } else {
                selectPerformanceTab();
            }
        }

        function selectOverviewTab() {
            closeSidebarOnMobile();
            activeTabId = 'overview';
            document.querySelectorAll('.stock-item').forEach(i => i.classList.remove('active'));
            document.querySelectorAll('.strategy-folder').forEach(f => f.classList.remove('active-folder'));
            const fold = document.getElementById('folder_overview');
            if (fold) fold.classList.add('active-folder');

            document.querySelectorAll('#main_panel .page').forEach(p => p.classList.remove('active'));
            const tabOver = document.getElementById('tab_overview');
            if (tabOver) tabOver.classList.add('active');

            updateStrategyOverviewUI();
        }

        function updateStrategyOverviewUI() {
            const badge = document.getElementById('overview_direction_badge');
            if (badge) {
                badge.textContent = activeDirection === 'long' ? '📈 多單策略' : '📉 空單策略';
                badge.style.background = activeDirection === 'long' ? 'rgba(99, 102, 241, 0.15)' : 'rgba(168, 85, 247, 0.15)';
                badge.style.color = activeDirection === 'long' ? '#4f46e5' : '#a855f7';
            }

            const startInput = document.getElementById('overview_start_date');
            const endInput = document.getElementById('overview_end_date');
            if (!startInput || !endInput) return;

            const startDateStr = startInput.value.replace(/-/g, '');
            const endDateStr = endInput.value.replace(/-/g, '');

            if (!startDateStr || !endDateStr) return;

            const filteredTrades = allTradesHistory.filter(t => {
                const isDirMatch = t.type === activeDirection;
                if (!isDirMatch) return false;
                const exitDate = String(t.exitDate || '').replace(/-/g, '');
                return exitDate >= startDateStr && exitDate <= endDateStr;
            });

            let totalProfit = 0;
            let totalRoi = 0;
            let winningTrades = 0;
            const totalTrades = filteredTrades.length;

            filteredTrades.forEach(t => {
                totalProfit += (t.pnl || 0);
                totalRoi += (t.roi || 0);
                if ((t.pnl || 0) > 0) winningTrades++;
            });

            const winRate = totalTrades > 0 ? (winningTrades / totalTrades * 100) : 0;
            const avgRoi = totalTrades > 0 ? (totalRoi / totalTrades) : 0;

            const profitEl = document.getElementById('overview_stat_profit');
            if (profitEl) {
                profitEl.textContent = (totalProfit >= 0 ? '+' : '') + totalProfit.toLocaleString() + ' 元';
                profitEl.style.color = totalProfit >= 0 ? '#10b981' : '#ef4444';
            }
            const winrateEl = document.getElementById('overview_stat_winrate');
            if (winrateEl) winrateEl.textContent = winRate.toFixed(1) + '%';
            const tradesEl = document.getElementById('overview_stat_trades');
            if (tradesEl) tradesEl.textContent = totalTrades + ' 次';
            const avgroiEl = document.getElementById('overview_stat_avgroi');
            if (avgroiEl) {
                avgroiEl.textContent = (avgRoi >= 0 ? '+' : '') + avgRoi.toFixed(2) + '%';
                avgroiEl.style.color = avgRoi >= 0 ? '#10b981' : '#ef4444';
            }

            const holdingsBody = document.querySelector('#overview_holdings_table tbody');
            if (holdingsBody) {
                holdingsBody.innerHTML = '';
                const filteredHoldings = Object.values(activeHoldings).filter(h => {
                    const hType = h.type || (h.posType === '空單' ? 'short' : 'long');
                    return hType === activeDirection;
                });

                if (filteredHoldings.length === 0) {
                    holdingsBody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:15px; color:#94a3b8;">📭 目前無持倉部位</td></tr>`;
                } else {
                    filteredHoldings.forEach(h => {
                        const tr = document.createElement('tr');
                        const pnlColor = h.pnl >= 0 ? '#10b981' : '#ef4444';
                        tr.innerHTML = `
                            <td style="padding:10px; font-weight:600;">\${h.code} \${h.name}</td>
                            <td style="padding:10px;"><span style="background:\${h.posType === '空單' ? 'rgba(168, 85, 247, 0.15)' : 'rgba(99, 102, 241, 0.15)'}; color:\${h.posType === '空單' ? '#a855f7' : '#4f46e5'}; padding:2px 8px; border-radius:12px; font-size:0.8rem; font-weight:700;">\${h.posType}</span></td>
                            <td style="padding:10px;">\${h.buyDate}</td>
                            <td style="padding:10px;">\${(h.buyPrice || 0).toFixed(2)}</td>
                            <td style="padding:10px;">\${(h.currentPrice || 0).toFixed(2)}</td>
                            <td style="padding:10px; font-weight:700; color:\${pnlColor};">\${(h.pnl >= 0 ? '+' : '') + h.pnl.toLocaleString()}</td>
                            <td style="padding:10px; font-weight:700; color:\${pnlColor};">\${(h.roi >= 0 ? '+' : '') + h.roi.toFixed(2)}%</td>
                            <td style="padding:10px;"><button onclick="const stk = preloadedStocks.find(s => s.id === '\${h.uniqueId}'); selectStockTab('\${h.uniqueId}', '\${h.code}', '\${h.name}', stk ? stk.strategy : 'ai_trend', 'preload')" style="padding:4px 8px; background:#4f46e5; color:white; border:none; border-radius:4px; font-size:0.8rem; cursor:pointer;">🔍 查看</button></td>
                        `;
                        holdingsBody.appendChild(tr);
                    });
                }
            }

            const historyBody = document.querySelector('#overview_history_table tbody');
            if (historyBody) {
                historyBody.innerHTML = '';
                if (filteredTrades.length === 0) {
                    historyBody.innerHTML = `<tr><td colspan="9" style="text-align:center; padding:30px; color:#94a3b8;">📭 選擇的日期區間內無交易記錄</td></tr>`;
                } else {
                    const displayList = [...filteredTrades].sort((a,b) => String(b.exitDate).localeCompare(String(a.exitDate)));
                    displayList.forEach(t => {
                        const tr = document.createElement('tr');
                        const pnlColor = t.pnl >= 0 ? '#10b981' : '#ef4444';
                        tr.innerHTML = `
                            <td style="padding:12px; font-weight:600;">\${t.code} \${t.name}</td>
                            <td style="padding:12px;"><span style="background:\${t.posType === '空單' ? 'rgba(168, 85, 247, 0.15)' : 'rgba(99, 102, 241, 0.15)'}; color:\${t.posType === '空單' ? '#a855f7' : '#4f46e5'}; padding:2px 8px; border-radius:12px; font-size:0.8rem; font-weight:700;">\${t.posType}</span></td>
                            <td style="padding:12px; font-size:0.85rem; color:#475569;">\${t.strategy}</td>
                            <td style="padding:12px;">\${t.entryDate}</td>
                            <td style="padding:12px;">\${(t.entryPrice || 0).toFixed(2)}</td>
                            <td style="padding:12px;">\${t.exitDate}</td>
                            <td style="padding:12px;">\${(t.exitPrice || 0).toFixed(2)}</td>
                            <td style="padding:12px; font-weight:700; color:\${pnlColor};">\${(t.pnl >= 0 ? '+' : '') + t.pnl.toLocaleString()}</td>
                            <td style="padding:12px; font-weight:700; color:\${pnlColor};">\${(t.roi >= 0 ? '+' : '') + t.roi.toFixed(2)}%</td>
                        `;
                        historyBody.appendChild(tr);
                    });
                }
            }
        }

        // 切換至績效排行榜"""
    if "// V8 交易方向與成績總覽邏輯" in html:
        start_js_idx = html.find("// V8 交易方向與成績總覽邏輯")
        end_js_idx = html.find("        // 切換至績效排行榜")
        if start_js_idx != -1 and end_js_idx != -1:
            old_js_block = html[start_js_idx:end_js_idx]
            html = html.replace(old_js_block, new_v8_functions)
            print("  [成功] 升級 V8.1 後台邏輯控制與統計運算函數 JS")
    else:
        if marker_function in html:
            html = html.replace(marker_function, new_v8_functions + marker_function)
            print("  [成功] 注入 V8.1 後台邏輯控制與統計運算函數 JS")

    # ── 9. 初始化結束日期為今日 ──
    old_init = "                // 6. 預設切換至績效排行榜"
    new_init = """                // 5.5 初始化總覽結束日期為今日 (V8)
                const endInput = document.getElementById('overview_end_date');
                if (endInput) endInput.value = new Date().toISOString().split('T')[0];

                // 6. 預設切換至績效排行榜"""
    if old_init in html and "overview_end_date" not in html:
        html = html.replace(old_init, new_init)
        print("  [成功] 注入結束日期初始化邏輯")

    # ── 10. 修改 `createCustomStockPage` 中 AI 策略的 Entry/Exit Options ──
    # 使其動態判斷 long/short 分別顯示多單/空單之 20/9 種策略選項
    old_ai_options = """            } else if (strategy.startsWith('ai_')) {
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
                ].map(opt => `<option value="${opt}" ${opt === defaultExit ? 'selected' : ''}>${opt}</option>`).join('');"""

    new_ai_options = """            } else if (strategy.startsWith('ai_')) {
                const stock = preloadedStocks.find(s => s.id === uniqueId);
                const isShortType = stock && (stock.type === 'short');
                const defaultEntry = stock ? stock.entry : (isShortType ? '弱勢均線空頭+KD死叉' : '強勢均線多頭+KD金叉');
                const defaultExit = stock ? stock.exit : '6%停利 / 6%停損 (穩健勝率)';
                const defaultTp = stock ? stock.tp : 6.0;
                const defaultSl = stock ? stock.sl : 6.0;
                
                const entryList = isShortType ? [
                    "弱勢均線空頭+KD死叉", "中長期空頭+RSI高檔轉弱", "雙重均線跌破+MACD翻綠", 
                    "EOM動能下跌+均線空頭", "極度超買共振 (BIAS+RSI+MFI)", "布林通道上軌+KD高檔死叉", 
                    "CCI超買+MFI超買+KD死叉", "雙重超買 (RSI+CCI)+MACD轉弱", "樞軸點(R1)壓力+KD死叉", 
                    "跌破支撐(S1)+MACD空頭", "跌破樞軸(Pivot)+RSI轉弱", "R1壓力不破+MACD綠柱增長", 
                    "空頭拉回：MA60之下+KD死叉+RSI>55", "布林中軌阻力+MACD綠柱", "動能共振：EOM下跌+MACD<0+RSI<50", 
                    "雙保險超買：BIAS超買+布林上軌觸及", "主力資金流出：MFI超買+EOM下跌", "支撐跌破：價格<S1+EOM弱勢+MACD<0", 
                    "長期均線阻力：跌破MA120+KD死叉+CCI超買", "CCI超買回檔+MACD綠柱增長"
                ] : [
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
                ];

                const exitList = isShortType ? [
                    "6%停利 / 6%停損 (穩健勝率)", "8%停利 / 8%停損 (均衡配置)", "12%停利 / 6%停損 (高盈虧比)",
                    "KD金叉離場或6%停損", "RSI超賣離場或6%停損", "MACD綠柱縮短離場或6%停損",
                    "收盤站上MA20或6%停損", "觸碰布林下軌停利或6%停損", "突破壓力(R1)或8%停利"
                ] : [
                    "6%停利 / 6%停損 (穩健勝率)",
                    "8%停利 / 8%停損 (均衡配置)",
                    "12%停利 / 6%停損 (高盈虧比)",
                    "KD死叉離場或6%停損",
                    "RSI超買離場或6%停損",
                    "MACD紅柱縮短離場或6%停損",
                    "收盤跌破MA20或6%停損",
                    "觸碰布林上軌停利或6%停損",
                    "跌破樞軸支撐(S1)或8%停利"
                ];

                const entryOptions = entryList.map(opt => `<option value="${opt}" ${opt === defaultEntry ? 'selected' : ''}>${opt}</option>`).join('');
                const exitOptions = exitList.map(opt => `<option value="${opt}" ${opt === defaultExit ? 'selected' : ''}>${opt}</option>`).join('');"""
    if old_ai_options in html:
        html = html.replace(old_ai_options, new_ai_options)
        print("  [成功] 修改 createCustomStockPage 以適配空單與多單策略的 Entry/Exit Options")

    # ── 11. 修改 `run_AI` 邏輯，使其完全支援 Short 模擬 ──
    old_run_ai_body = """            // 預計算所有訊號陣列，加速回測
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
            }"""

    new_run_ai_body = """            // 預計算所有訊號陣列，加速回測
            const entrySignals = new Array(ds.length).fill(false);
            const exitSignals = new Array(ds.length).fill(false);
            
            // V8 檢測是否為空單策略
            const stockInfo = preloadedStocks.find(s => s.id === uniqueId);
            const isShort = stockInfo && (stockInfo.type === 'short');
            
            for (let i = 1; i < ds.length; i++) {
                const c = ds[i];
                const prev = ds[i-1];
                
                if (!isShort) {
                    // 多單指標計算
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
                } else {
                    // 空單指標計算 (V8)
                    let f_ma_bear = (c.ma5 < c.ma20) && (c.ma20 < c.ma60);
                    let f_below_pivot = c.close < c.pivot;
                    let f_break_s1 = (c.close < c.s1) && (c.s1 > 0);
                    let f_bias_overbought = c.bias20 > 4;
                    let f_cci_overbought = c.cci > 100;
                    let f_eom_bearish = c.eom < c.eomSig;
                    let f_mfi_overbought = c.mfi > 70;
                    let f_bb_overbought_short = (c.close > c.bb_upper) && (c.bb_upper > 0);
                    
                    let f_kd_dead = (c.k < c.d) && (prev.k >= prev.d);
                    let f_rsi_overbought = c.rsi > 65;
                    let f_macd_shrink = c.macd < prev.macd;
                    let f_below_ma20 = c.close < c.ma20;
                    let f_below_ma60 = c.close < c.ma60;
                    let f_below_ma120 = c.close < c.ma120;
                    
                    let condShort = false;
                    if (entryStrat === "弱勢均線空頭+KD死叉") condShort = f_ma_bear && f_kd_dead && f_below_ma20;
                    else if (entryStrat === "中長期空頭+RSI高檔轉弱") condShort = f_below_ma60 && f_below_ma120 && (c.rsi > 55) && f_macd_shrink;
                    else if (entryStrat === "雙重均線跌破+MACD翻綠") condShort = f_below_ma20 && f_below_ma60 && (c.macd < 0) && f_macd_shrink;
                    else if (entryStrat === "EOM動能下跌+均線空頭") condShort = f_eom_bearish && f_ma_bear && f_below_ma20;
                    else if (entryStrat === "極度超買共振 (BIAS+RSI+MFI)") condShort = f_bias_overbought && f_rsi_overbought && f_mfi_overbought;
                    else if (entryStrat === "布林通道上軌+KD高檔死叉") condShort = f_bb_overbought_short && f_kd_dead;
                    else if (entryStrat === "CCI超買+MFI超買+KD死叉") condShort = f_cci_overbought && f_mfi_overbought && f_kd_dead;
                    else if (entryStrat === "雙重超買 (RSI+CCI)+MACD轉弱") condShort = f_rsi_overbought && f_cci_overbought && f_macd_shrink;
                    else if (entryStrat === "樞軸點(R1)壓力+KD死叉") condShort = (c.close < c.r1) && (c.high >= c.r1) && f_kd_dead && (c.r1 > 0);
                    else if (entryStrat === "跌破支撐(S1)+MACD空頭") condShort = f_break_s1 && (c.macd < 0) && f_below_ma20;
                    else if (entryStrat === "跌破樞軸(Pivot)+RSI轉弱") condShort = f_below_pivot && (c.rsi < 50) && f_macd_shrink;
                    else if (entryStrat === "R1壓力不破+MACD綠柱增長") condShort = (c.close < c.r1) && f_macd_shrink && (c.r1 > 0);
                    else if (entryStrat === "空頭拉回：MA60之下+KD死叉+RSI>55") condShort = f_below_ma60 && f_kd_dead && (c.rsi > 55);
                    else if (entryStrat === "布林中軌阻力+MACD綠柱") condShort = (c.close > c.bb_lower) && (c.close < c.bb_upper) && f_below_ma20 && f_macd_shrink;
                    else if (entryStrat === "動能共振：EOM下跌+MACD<0+RSI<50") condShort = f_eom_bearish && (c.macd < 0) && (c.rsi < 50);
                    else if (entryStrat === "雙保險超買：BIAS超買+布林上軌觸及") condShort = f_bias_overbought && f_bb_overbought_short;
                    else if (entryStrat === "主力資金流出：MFI超買+EOM下跌") condShort = f_mfi_overbought && f_eom_bearish;
                    else if (entryStrat === "支撐跌破：價格<S1+EOM弱勢+MACD<0") condShort = f_break_s1 && f_eom_bearish && (c.macd < 0);
                    else if (entryStrat === "長期均線阻力：跌破MA120+KD死叉+CCI超買") condShort = (c.close < c.ma120) && f_kd_dead && f_cci_overbought;
                    else if (entryStrat === "CCI超買回檔+MACD綠柱增長") condShort = f_cci_overbought && f_macd_shrink && f_below_ma20;
                    
                    entrySignals[i] = condShort;
                    
                    // 空單平倉訊號
                    let f_kd_gold_cover = (c.k > c.d) && (prev.k <= prev.d);
                    let f_rsi_oversold_cover = c.rsi < 35;
                    let f_macd_grow_cover = c.macd > prev.macd;
                    let f_above_ma20_cover = c.close > c.ma20;
                    let f_bb_oversold_cover = (c.close < c.bb_lower) && (c.bb_lower > 0);
                    let f_above_r1_cover = (c.close > c.r1) && (c.r1 > 0);
                    
                    let condExit = false;
                    if (exitStrat === "KD死叉離場或6%停損" || exitStrat === "KD金叉離場或6%停損") condExit = f_kd_gold_cover;
                    else if (exitStrat === "RSI超買離場或6%停損" || exitStrat === "RSI超賣離場或6%停損") condExit = f_rsi_oversold_cover;
                    else if (exitStrat === "MACD紅柱縮短離場或6%停損" || exitStrat === "MACD綠柱縮短離場或6%停損") condExit = f_macd_grow_cover;
                    else if (exitStrat === "收盤跌破MA20或6%停損" || exitStrat === "收盤站上MA20或6%停損") condExit = f_above_ma20_cover;
                    else if (exitStrat === "觸碰布林上軌停利或6%停損" || exitStrat === "觸碰布林下軌停利或6%停損") condExit = f_bb_oversold_cover;
                    else if (exitStrat === "跌破樞軸支撐(S1)或8%停利" || exitStrat === "突破壓力(R1)或8%停利") condExit = f_above_r1_cover;
                    
                    exitSignals[i] = condExit;
                }
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
                        trd.push({ type: isShort ? '放空' : '買入', date: n.date, price: bp, info: 'AI 進場訊號觸發' });
                    }
                } else {
                    const pnlR = isShort ? (bp - n.open) / bp : (n.open - bp) / bp;
                    
                    // 停利停損檢查
                    const cond_tp = (tp !== null) && (pnlR >= tp);
                    const cond_sl = (sl !== null) && (pnlR <= -sl);
                    const cond_sig = exitSignals[i];
                    
                    if (cond_tp || cond_sl || cond_sig) {
                        hold = false;
                        const ep = n.open;
                        const p = isShort ? (bp - ep) * sh : (ep - bp) * sh;
                        tot += p;
                        si[i+1] = 1;
                        
                        let infoStr = 'AI 出場條件觸發';
                        if (cond_tp) infoStr = 'AI 停利出口';
                        else if (cond_sl) infoStr = 'AI 停損出口';
                        
                        trd.push({ type: isShort ? '回補' : '賣出', date: n.date, price: ep, info: infoStr, pnl: p, entP: bp });
                    }
                }
            }"""
    if old_run_ai_body in html:
        html = html.replace(old_run_ai_body, new_run_ai_body)
        print("  [成功] 修改 run_AI 回測主引擎支援雙向交易模擬")

    # ── 12. 修改 `updateUI` 支援 `isShortHolding` ──
    old_is_short_holding = "            const isShortHolding = lastTrd && lastTrd.type === '賣出' && lastTrd.info.includes('空單進場');"
    new_is_short_holding = "            const isShortHolding = lastTrd && (lastTrd.type === '放空' || (lastTrd.type === '賣出' && lastTrd.info.includes('空單進場')));"
    if old_is_short_holding in html:
        html = html.replace(old_is_short_holding, new_is_short_holding)
        print("  [成功] 修改 updateUI 支援 V8 AI 空單持倉判定")

    with open(HTML_PATH, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"\n[完成] 所有 V8 邏輯修改已成功注入 {HTML_PATH}！")
    print("=" * 60)

if __name__ == "__main__":
    main()
