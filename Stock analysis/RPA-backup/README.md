# 股票看盤軟體 RPA 自動化匯出腳本

> 適用：**台新贏家快手 V5.1.1**  
> 功能：自動輸入股票代碼 → K線圖右鍵匯出 Excel → 清洗箭頭符號 → 儲存指定路徑

---

## 📁 檔案結構

```
RPA_Automation/
├── stock_exporter.py       ← 主程式（完整 RPA 模式 + 純清洗模式）
├── get_coordinates.py      ← 座標測量工具（測量點擊位置用）
├── find_menu_offset.py     ← 右鍵選單偏移量測量工具
├── test_cleaner.py         ← 箭頭清洗函數單元測試
└── README.md               ← 本說明文件
```

---

## ⚙️ 安裝套件

```bash
pip install pyautogui pandas openpyxl pyperclip
```

---

## 🚀 使用步驟

### Step 1：測量座標（只需做一次）

**測量 K 線圖右鍵點擊位置：**
```bash
python get_coordinates.py
```
移動滑鼠到 K 線圖中央位置，記錄顯示的 `(X, Y)` 座標。

**測量右鍵選單「匯出至 Excel」的偏移量：**
```bash
python find_menu_offset.py
```
按照提示操作，程式會自動計算偏移量。

### Step 2：修改設定

開啟 `stock_exporter.py`，找到 `CONFIG` 區塊並修改：

```python
CONFIG = {
    # 要匯出的股票代碼清單
    "stock_list": ["2330", "6261", ...],

    # 股票中文名稱對照（用於存檔命名）
    "stock_names": {"2330": "台積電", ...},

    # 清洗後 Excel 的儲存位置
    "output_folder": r"E:\G-AI-1\Stock analysis\Stock original\auto_export",

    # K線圖右鍵點擊座標（Step 1 測量的結果）
    "kline_right_click_pos": (960, 500),

    # 右鍵選單「匯出至 Excel」的 Y 軸偏移（Step 1 測量的結果）
    "export_menu_offset_y": 80,
}
```

### Step 3：驗證清洗函數

```bash
python test_cleaner.py
```

確認輸出全部顯示 `✅ PASS`。

### Step 4：執行主程式

**完整 RPA 模式（自動操作看盤軟體）：**
```bash
python stock_exporter.py
```

切換到看盤軟體後，5 秒倒數結束後自動開始操作。

**純清洗模式（已手動匯出 Excel，只需清洗）：**
```bash
python stock_exporter.py clean
```

---

## 🔤 箭頭符號清洗說明

腳本會自動清除以下箭頭符號：

| 符號 | Unicode | 範例輸入 | 清洗輸出 |
|------|---------|---------|---------|
| ▲ | U+25B2 | `82.5▲` | `82.5` |
| ▼ | U+25BC | `12.3▼` | `12.3` |
| ↑ | U+2191 | `100↑` | `100.0` |
| ↓ | U+2193 | `-5.6↓` | `-5.6` |
| △ | U+25B3 | `0△` | `0.0` |
| ▽ | U+25BD | `99.9▽` | `99.9` |

清洗後的欄位會**自動轉換為 float 浮點數**，可直接用於數學運算。

---

## 📂 輸出檔案命名格式

```
{股票代碼}_{股票名稱}_EOM_{日期}.xlsx

範例：
  2330_台積電_EOM_20260611.xlsx
  6261_久元_EOM_20260611.xlsx
```

這與系統 `dashboard_v5.html` 的 `parseData` 函數相容。

---

## ⚠️ 注意事項

1. **緊急中止**：執行時將滑鼠快速移到螢幕**左上角**，PyAutoGUI 會自動停止
2. **執行期間**請勿移動滑鼠或觸碰鍵盤
3. 每支股票處理間隔約 **5~8 秒**，12 支股票約需 **1~2 分鐘**
4. 若看盤軟體反應較慢，請調高 `wait_after_stock_change` 的值
5. 右鍵選單的位置可能因**視窗大小或螢幕解析度**不同而變化，需重新測量

---

## 🔧 調整時間參數

若發現操作速度太快（選單來不及出現）或太慢，修改 CONFIG 中的等待時間：

```python
"wait_after_stock_change": 2.0,  # 換股後等待 K 線刷新（秒）
"wait_after_right_click": 0.8,   # 右鍵選單彈出等待（秒）
"wait_for_dialog": 1.5,          # 另存新檔對話框等待（秒）
"wait_after_export": 2.0,        # 匯出寫入完成等待（秒）
```

---

## 🔗 與 dashboard_v5.html 的整合

匯出的 Excel 可直接上傳至系統的「➕ 載入」功能，每個策略（V4/Rebound/DipBuy/V38）皆可獨立分析同一支個股。
