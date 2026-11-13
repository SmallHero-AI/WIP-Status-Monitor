# RO Survivors (RO 倖存者) 自動遊玩機器人

專為網頁版 [RO Survivors (ro-survivors.com)](https://ro-survivors.com/#playinnow-ro-zh-tw) 設計的全自動掛機遊玩機器人。採用 Node.js 與 Playwright 瀏覽器自動化技術，具備智慧走位避障、AI 技能配點、自適應推關與防卡死看門狗機制。

---

## 特色與核心功能

1. **全自動掛機循環**：
   - 自動登入：自動填入設定之帳號與密碼，並處理進入遊戲流程。
   - 自適應推關：若通關成功自動進入下一關；若挑戰失敗則停留在原關卡持續重試與刷資源。
   - 死後與結算重啟：戰鬥結束（勝利或陣亡）自動點選確認並啟動下一局。
2. **動態人工勢場 (Potential Field) 風箏走位**：
   - 模擬高階玩家的自然風箏拉怪節奏，動態計算避障與引力向量，以平滑的 WASD 鍵盤控制角色走位。
3. **AI 啟發式技能挑選引擎**：
   - 升級選卡彈窗出現時，AI 自動評估備選卡片之 AOE 清怪、生存回血與後期攻擊/冷卻權重，挑選最佳流派技能。
4. **高穩定性防卡死看門狗 (Watchdog)**：
   - 內建 60 秒無響應偵測，若因網路波動或未知彈窗卡住，自動重新整理頁面、重新登入並接續掛機。
5. **終端機即時儀表板**：
   - 即時統計總局數、勝場、敗場、勝率、當前關卡、最佳存活秒數與累計運行時長。

---

## 專案結構

```text
e:\G-AI-1\ro_survivor_bot/
├── .env                      # 帳號密碼與網址環境變數 (請勿外流)
├── .env.example              # 環境變數範本
├── .gitignore                # Git 忽略設定
├── package.json              # 專案依賴與啟動腳本
├── config.json               # 遊戲設定檔 (推關、技能優先度、走位參數)
├── README.md                 # 專案使用說明
└── src/
    ├── index.js              # 主程式進入點 (生命週期與狀態機調度)
    ├── browser.js            # Playwright 瀏覽器實例管理
    ├── auth.js               # 自動登入與身分驗證
    ├── navigator.js          # 大廳導航與自適應關卡選擇
    ├── settlement.js         # 勝負結算與自適應關卡遞進
    ├── watchdog.js           # 60 秒防卡死計時器
    ├── logger.js             # 彩色終端機即時統計輸出
    └── combat/
        ├── stateDetector.js  # 遊戲畫面狀態偵測 (戰鬥/升級/結算/大廳)
        ├── movement.js       # 人工勢場避障與鍵盤控制
        └── skillPicker.js    # AI 智慧技能卡片評分決策模組
```

---

## 安裝與快速啟動

### 1. 安裝環境依賴 (首次執行)
本專案已完成安裝，若更換環境可執行：
```powershell
cd e:\G-AI-1\ro_survivor_bot
npm.cmd install
npx.cmd playwright install chromium
```

### 2. 帳號設定 (`.env`)
專案目錄下的 `.env` 檔案已設定預設帳密：
```ini
GAME_URL=https://ro-survivors.com/#playinnow-ro-zh-tw
GAME_ACCOUNT=SmallHero
GAME_PASSWORD=0982286057
HEADLESS=false
```

### 3. 啟動機器人

- **可視化視窗模式 (預設，推薦初次觀察使用)**：
  ```powershell
  cd e:\G-AI-1\ro_survivor_bot
  npm.cmd start
  ```

- **背景無頭模式 (Headless，省資源安靜掛機)**：
  ```powershell
  cd e:\G-AI-1\ro_survivor_bot
  npm.cmd run start:headless
  ```

---

## 進階自訂設定 (`config.json`)

在 `config.json` 中可自由微調參數：
- `progression.adaptive`：設為 `true` 啟用自適應推關（通關前進、失敗原關重試）；設為 `false` 鎖定在 `currentStage`。
- `combat.kitingRadius`：風箏走位的基礎半徑。
- `skills.priorityKeywords`：技能優先度關鍵字清單，越靠前的關鍵字在升級時享有越高的 AI 權重加成。

