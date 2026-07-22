# Stock analysis 專案修改 SOP

當在 `Stock analysis` 目錄底下進行任何程式碼修改或開發時，必須嚴格遵守以下標準作業程序 (SOP)，以避免破壞高度耦合的資料流水線架構：

1. **欄位名稱相依性 (技術指標新增/修改)**：
   若需新增或修改任何技術指標，必須嚴格遵循以下順序，進行一條龍的修改：
   - **第一步**：修改資料獲取端 `download_stock_data.py`，確保計算邏輯與輸出的 CSV 欄位名稱正確。
   - **第二步**：同步修改回測引擎 `search_75_winrate_*.py` 內的欄位匹配邏輯 (如 `find_column`) 及策略運算邏輯。
   - **第三步**：同步修改匯出模組 `export_high_win_excel_*.py`，確保能正確對應欄位以利匯出。
   **嚴禁只修改單一腳本而未同步檢查並更新其他依賴該欄位的腳本。**

2. **JSON 資料結構的一致性**：
   回測引擎 (`search_75_winrate_*.py`) 所匯出的 `leaderboard` 及 `trades` JSON 結構是連接前後端的唯一橋樑。
   - 若修改了 JSON 的結構（如更改 Key 名稱或增加結構層級），**必須同步修改**前端 Web 儀表板 (如 `dashboard_v8_4.html`) 以及 Node.js 伺服器 (`server.js`) 中的解析邏輯，否則前端畫面將無法正確渲染。

3. **版本號的一致性**：
   專案內存在多個版本分支 (如 `v8`, `v8_1`, `v8_2`, `v8_3`, `v8_4`)。
   - 執行或修改腳本時，必須確保**同一條執行流程中，所有的相關腳本與檔案均對齊同一個版號**。
   - 例如：修改 `v8_4` 版本，就必須同時修改 `search_75_winrate_v8_4.py`、`export_high_win_excel_v8_4.py`、`update_and_push_v8_4.py` 以及 `dashboard_v8_4.html`。
   - **新增策略時**：需確保回測腳本中的策略清單 (`long_entry_names`, `short_entry_names` 等) 與匯出腳本中的買賣訊號判斷邏輯 **100% 完全對齊**。

此 SOP 為強制規範，任何 AI 代理在處理 `Stock analysis` 相關任務時都必須優先閱讀並遵守。
