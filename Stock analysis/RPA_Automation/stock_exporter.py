# -*- coding: utf-8 -*-
"""
================================================================================
  台新贏家快手 V5.1.1  RPA 自動化匯出腳本（精確座標版 v2）
  
  修正：加入明確的 duration 讓滑鼠移動可見、強化 log 輸出
  修正：使用 win32gui 處理台新贏家快手「隱藏至螢幕外」特殊狀態
        透過 PostMessage(WM_SYSCOMMAND, SC_RESTORE) 強制還原視窗
================================================================================
"""

import pyautogui
import pygetwindow as gw
import win32gui
import win32con
import win32api
import time
import os
import re
import glob
import pandas as pd
from datetime import datetime
import win32com.client
import json
import shutil
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass
if sys.stderr.encoding != 'utf-8':
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass


# ======================== PyAutoGUI 安全設定 ========================
pyautogui.FAILSAFE = True
# 注意：PAUSE 設為 0 可讓我們手動控制每步的等待時間
pyautogui.PAUSE = 0.0


# ======================== 精確座標（已由使用者校準）========================
COORD = {
    "stock_search"     : (155, 125),   # Step1 搜尋框
    "kline_right_click": (500, 200),   # Step2 K線圖右鍵
    "export_menu"      : (550, 475),   # Step2 匯出選單
}

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "coords_config.json")

# 載入自訂座標設定 (若有)
if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            saved_coords = json.load(f)
            for k, v in saved_coords.items():
                if k in COORD:
                    COORD[k] = tuple(v)
    except Exception:
        pass


# 自動解析相對路徑，讓資料夾隨意複製到任何硬碟皆可執行
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STOCK_ANALYSIS_DIR = os.path.dirname(SCRIPT_DIR)

OUTPUT_FOLDER = os.path.join(STOCK_ANALYSIS_DIR, "Stock original", "auto_export")
DATE_TODAY    = datetime.now().strftime("%Y%m%d")


# 預設備用名單
STOCK_LIST = [
    {"code": "2330", "name": "台積電"},
    {"code": "2360", "name": "致茂"},
    {"code": "6205", "name": "詮欣"},
    {"code": "6274", "name": "台耀"},
    {"code": "6669", "name": "緯穎"},
    {"code": "3189", "name": "景碩"},
    {"code": "3455", "name": "由田"},
    {"code": "3535", "name": "晶彩科"},
    {"code": "4908", "name": "前鼎"},
    {"code": "6269", "name": "台郡"},
    {"code": "3443", "name": "創意"},
    {"code": "6261", "name": "久元"},
]

EXCEL_STOCK_LIST_PATH = os.path.join(STOCK_ANALYSIS_DIR, "Stock original", "有價證券代號與名稱.xlsx")

if os.path.exists(EXCEL_STOCK_LIST_PATH):
    try:
        df_list = pd.read_excel(EXCEL_STOCK_LIST_PATH, header=0)
        loaded_stocks = []
        for idx, row in df_list.iterrows():
            code = str(row.iloc[0]).strip()
            name = str(row.iloc[1]).strip()
            if code and name and code.isdigit():
                loaded_stocks.append({"code": code, "name": name})
        if loaded_stocks:
            STOCK_LIST = loaded_stocks
    except Exception as e:
        pass


# ======================== 時間參數 ========================
WAIT = {
    "kline_refresh"  : 2.0,   # 換股後等待 K 線刷新
    "menu_popup"     : 0.8,   # 右鍵選單彈出等待
    "excel_open"     : 4.0,   # 等待 Excel 自動開啟
    "window_switch"  : 0.8,   # 視窗切換穩定等待
    "excel_close"    : 1.5,   # Excel 關閉後等待
    "between_stocks" : 1.0,   # 每支個股間隔
}

MOUSE_DURATION = 0.4   # 滑鼠移動動畫時間（秒），設 0 則瞬間移動


# ================================================================
#  工具函數
# ================================================================

def log(step, msg):
    """格式化輸出 log，方便追蹤執行狀態，同時寫入檔案"""
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"  [{ts}] {step} {msg}"
    print(line, flush=True)
    try:
        log_path = os.path.join(SCRIPT_DIR, "stock_exporter.log")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except:
        pass



def clean_value(value):
    """
    清除箭頭符號並轉換為 float。
    支援：▲ ▼ ↑ ↓ △ ▽ 及其他方向符號、千分位逗號
    """
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    text = str(value).strip()
    if not text:
        return None

    # 移除所有常見箭頭符號
    cleaned = re.sub(r'[▲▼↑↓△▽➚➘➙➛➜→←↗↘↙↖➡⬆⬇⬅]', '', text).strip()
    cleaned = cleaned.replace(',', '')  # 移除千分位

    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def move_and_click(x, y, button='left', label=''):
    """
    將滑鼠移動到指定座標後點擊。
    使用 duration 讓移動過程可見（0.4 秒動畫）。
    """
    log('🖱 ', f"移動到 ({x}, {y}) {label}")
    pyautogui.moveTo(x, y, duration=MOUSE_DURATION)
    time.sleep(0.1)   # 讓滑鼠「定位」後再點擊

    if button == 'right':
        log('🖱 ', f"右鍵點擊 ({x}, {y})")
        pyautogui.rightClick()
    else:
        log('🖱 ', f"左鍵點擊 ({x}, {y})")
        pyautogui.click()

    time.sleep(0.15)


def find_winner_hwnd():
    """
    用 win32gui 搜尋台新贏家快手的視窗 handle（hwnd）。
    支援視窗在螢幕外（-32000,-32000）的特殊最小化狀態。
    工作管理員中的應用程式名稱：HTS Kway Corporation

    Returns:
        int hwnd 或 None
    """
    # 所有可能的標題關鍵字（含工作管理員名稱、中英文）
    KEYWORDS = ['贏家', 'HTS', 'Kway', 'kway', 'Winner', 'winner', '快手', '台新']

    result = []
    def cb(hwnd, _):
        try:
            title = win32gui.GetWindowText(hwnd)
            if not title.strip():
                return
            for kw in KEYWORDS:
                if kw in title:
                    result.append((hwnd, title))
                    return
        except Exception:
            pass
    win32gui.EnumWindows(cb, None)

    if not result:
        return None

    # 優先選擇有實際大小的主視窗（非工作列縮圖）
    for hwnd, title in result:
        rect = win32gui.GetWindowRect(hwnd)
        l, t, r, b = rect
        if r - l > 400:   # 寬度 > 400px 視為主視窗
            return hwnd

    # 若都是小視窗（最小化狀態），回傳第一個
    return result[0][0] if result else None


def force_restore_winner(hwnd):
    """
    強制還原台新贏家快手視窗（適用隱藏至螢幕外的特殊狀態）。
    使用 PostMessage(WM_SYSCOMMAND, SC_RESTORE) 而非 ShowWindow，
    因為後者對此軟體的特殊最小化無效。

    Returns:
        bool: 是否成功還原至螢幕可見區域
    """
    log('🪟', f"強制還原台新贏家快手 (hwnd={hwnd})")

    # 先用各種 ShowWindow 方式嘗試
    for sw_cmd in [win32con.SW_RESTORE, win32con.SW_SHOWNORMAL, win32con.SW_SHOW]:
        win32gui.ShowWindow(hwnd, sw_cmd)
        time.sleep(0.3)
        rect = win32gui.GetWindowRect(hwnd)
        l, t, r, b = rect
        if l > -1000 and r - l > 400:
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(0.3)
            log('✅', f"ShowWindow 成功，位置=({l},{t})，大小={(r-l)}x{(b-t)}")
            return True

    # 備用：PostMessage WM_SYSCOMMAND SC_RESTORE（對此軟體有效）
    win32api.PostMessage(hwnd, win32con.WM_SYSCOMMAND, win32con.SC_RESTORE, 0)
    time.sleep(0.8)
    rect = win32gui.GetWindowRect(hwnd)
    l, t, r, b = rect
    if l > -1000 and r - l > 400:
        try:
            win32gui.SetForegroundWindow(hwnd)
        except Exception:
            pass
        time.sleep(0.3)
        log('✅', f"WM_SYSCOMMAND 成功，位置=({l},{t})，大小={(r-l)}x{(b-t)}")
        return True

    log('❌', f"所有還原方法失敗，位置仍為 ({l},{t})")
    return False


def focus_winner_safely(hwnd):
    """
    安全聚焦視窗：如果已在螢幕上，僅進行 SetForegroundWindow，絕不移動或縮放視窗。
    只有在最小化或在螢幕外時才進行還原。
    """
    try:
        # IsIconic 檢查是否最小化
        if win32gui.IsIconic(hwnd):
            log('🪟', "偵測到視窗最小化，進行還原...")
            force_restore_winner(hwnd)
            return True
            
        rect = win32gui.GetWindowRect(hwnd)
        l, t, r, b = rect
        if l < -100 or r - l < 400:
            log('🪟', "偵測到視窗在螢幕外，進行還原...")
            force_restore_winner(hwnd)
            return True
            
        # 視窗已經在螢幕上，僅做 SetForegroundWindow 避免移動/縮放
        log('🪟', f"視窗已在螢幕上，直接聚焦 (不移動/縮放)。目前位置: ({l},{t})")
        try:
            win32gui.SetForegroundWindow(hwnd)
        except Exception as e:
            log('⚠️ ', f"SetForegroundWindow 失敗: {e}")
        return True
    except Exception as e:
        log('❌', f"安全聚焦失敗: {e}")
        return False


def find_excel_window(timeout=8.0):
    """等待並找到 Excel 視窗（含超時）"""
    log('🔍', f"尋找 Excel 視窗（最多等 {timeout} 秒）...")
    deadline = time.time() + timeout
    while time.time() < deadline:
        wins = gw.getWindowsWithTitle('Excel')
        if wins:
            log('✅', f"找到 Excel：{wins[0].title}")
            return wins[0]
        for win in gw.getAllWindows():
            t = win.title
            if '.xlsx' in t or '.xls' in t or 'Microsoft Excel' in t:
                log('✅', f"找到 Excel：{t}")
                return win
        time.sleep(0.5)
    log('⚠️ ', "超時未找到 Excel 視窗")
    return None


def activate_win(win, label):
    """激活視窗（還原最小化 + 聚焦）"""
    if win is None:
        log('⚠️ ', f"找不到「{label}」視窗")
        return False
    try:
        if win.isMinimized:
            win.restore()
            time.sleep(0.3)
        win.activate()
        time.sleep(WAIT["window_switch"])
        log('✅', f"已切換至「{label}」")
        return True
    except Exception as e:
        log('❌', f"切換至「{label}」失敗：{e}")
        return False


def find_latest_excel_after(ts):
    """搜尋 ts 時間點後產生的最新 Excel 暫存檔 (含 .txt)"""
    dirs = [
        r"C:\ML_Speed\user",
        os.path.expanduser("~/Desktop"),
        os.path.expanduser("~/Documents"),
        os.path.expanduser("~/Downloads"),
        os.environ.get('TEMP', ''),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Temp'),
        r"C:\Users\loadmin\Desktop",
        r"C:\Users\loadmin\Documents",
        r"C:\Users\loadmin\Downloads",
    ]
    newest, newest_ts = None, ts
    for d in dirs:
        if not d or not os.path.exists(d):
            continue
        for ext in ['*.xlsx', '*.xls', '*.txt']:
            for f in glob.glob(os.path.join(d, ext)):
                try:
                    mt = os.path.getmtime(f)
                    if mt > newest_ts:
                        newest_ts, newest = mt, f
                except OSError:
                    pass
    return list_dir_check(newest) if newest else None

def list_dir_check(path):
    # Helper to print found file info
    try:
        log('📄', f"找到暫存檔案：{path} (大小: {os.path.getsize(path)} bytes)")
    except:
        pass
    return path


# ================================================================
#  五步驟流程
# ================================================================

def step1_input_stock(code, name):
    """
    Step1：點擊搜尋框 → 清空 → 輸入4碼代號 → Enter → 等待刷新
    """
    log('📌 STEP1', f"輸入股號 {code} {name}")

    # 移動並點擊搜尋框
    move_and_click(*COORD["stock_search"], label="[搜尋框]")

    # 全選清空現有文字
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.1)
    pyautogui.hotkey('ctrl', 'a')   # 雙重確認全選
    time.sleep(0.1)

    # 逐字輸入代號
    log('⌨️ ', f"輸入代號：{code}")
    pyautogui.typewrite(code, interval=0.15)
    time.sleep(0.2)

    # 確認換股
    log('⌨️ ', "按下 Enter")
    pyautogui.press('enter')

    log('⏳', f"等待 K 線刷新 {WAIT['kline_refresh']} 秒...")
    time.sleep(WAIT["kline_refresh"])
    log('✅', "Step1 完成")


def step2_export_excel():
    """
    Step2：K線圖右鍵 → 點選「匯出至 Excel」
    Return: 匯出前時間戳
    """
    log('📌 STEP2', "右鍵匯出 Excel")

    before = time.time()

    # 右鍵點擊 K 線圖
    move_and_click(*COORD["kline_right_click"], button='right', label="[K線圖]")
    log('⏳', f"等待右鍵選單彈出 {WAIT['menu_popup']} 秒...")
    time.sleep(WAIT["menu_popup"])

    # 點擊「匯出至 Excel」
    move_and_click(*COORD["export_menu"], label="[匯出 Excel 選單項]")
    log('⏳', f"等待 Excel 開啟 {WAIT['excel_open']} 秒...")
    time.sleep(WAIT["excel_open"])

    log('✅', "Step2 完成")
    return before


def step3_switch_and_clean_com(before_ts, code, name):
    """
    Step3 & Step4：使用 Excel COM 自動化進行欄位清洗（將 ↑ 與 ↓ 取代為空白）並另存為 CSV，最後關閉。
    """
    log('📌 STEP3 & 4', "Excel COM 自動化：清洗箭頭並另存 CSV")

    # 1. 確保 Excel 視窗已出現
    excel_win = find_excel_window(timeout=10.0)
    if not excel_win:
        log('❌', "找不到 Excel 視窗！")
        return False

    # 確保 Excel 視窗在前景，給予穩定時間
    activate_win(excel_win, "Excel")
    time.sleep(1.0)

    # 2. 獲取 Excel COM 物件
    excel_app = None
    for i in range(15):
        try:
            excel_app = win32com.client.GetActiveObject("Excel.Application")
            if excel_app and excel_app.Workbooks.Count > 0:
                break
        except Exception:
            pass
        time.sleep(0.5)

    if not excel_app:
        log('❌', "無法取得作用中的 Excel 應用程式實例 (COM)")
        return False

    try:
        excel_app.DisplayAlerts = False

        # 3. 尋找對應的活頁簿
        wb = None
        for w in excel_app.Workbooks:
            if code in w.Name:
                wb = w
                break
        if not wb:
            log('⚠️ ', f"找不到檔名含 {code} 的活頁簿，將使用目前作用中的活頁簿")
            wb = excel_app.ActiveWorkbook

        if not wb:
            log('❌', "無法取得作用中的 Excel 活頁簿！")
            return False

        log('📄', f"已取得活頁簿：{wb.Name}")
        ws = wb.ActiveSheet

        # 4. 執行取代：將 ↑ 與 ↓ 取代為空白
        log('🧹', "在 Excel 執行取代：將 ↑ 取代為空白")
        ws.Cells.Replace(What="↑", Replacement="", LookAt=2, SearchOrder=1, MatchCase=False)
        log('🧹', "在 Excel 執行取代：將 ↓ 取代為空白")
        ws.Cells.Replace(What="↓", Replacement="", LookAt=2, SearchOrder=1, MatchCase=False)

        # 5. 儲存為 CSV
        os.makedirs(OUTPUT_FOLDER, exist_ok=True)
        csv_name = f"{code}_{name}_{DATE_TODAY}.csv"
        csv_path = os.path.join(OUTPUT_FOLDER, csv_name)

        # 如果已經存在，先刪除以避免覆蓋提示
        if os.path.exists(csv_path):
            try:
                os.remove(csv_path)
            except Exception:
                pass

        log('💾', f"另存為 CSV 格式：{csv_path}")
        # FileFormat=6 代表 xlCSV
        wb.SaveAs(Filename=csv_path, FileFormat=6)

        # 6. 關閉活頁簿
        wb.Close(SaveChanges=False)
        log('✅', f"已成功儲存並關閉活頁簿")

        # 7. 若無其他活頁簿，關閉整個 Excel 應用程式
        if excel_app.Workbooks.Count == 0:
            excel_app.Quit()
            log('✅', "Excel 應用程式已關閉")

        return True
    except Exception as e:
        log('❌', f"Excel COM 處理失敗：{e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            if excel_app:
                excel_app.DisplayAlerts = True
        except Exception:
            pass



def step5_back_to_winner():
    """
    Step5：切換回台新贏家快手視窗（安全聚焦）
    準備輸入下一支個股代號
    """
    log('📌 STEP5', "切換回台新贏家快手")

    hwnd = find_winner_hwnd()
    if hwnd:
        focus_winner_safely(hwnd)
        time.sleep(0.5)
    else:
        log('⚠️ ', "未找到視窗，使用 Alt+Tab")
        pyautogui.hotkey('alt', 'tab')
        time.sleep(WAIT["window_switch"])

    log('✅', "Step5 完成，準備下一支")


def calibrate_coordinates():
    """
    即時顯示滑鼠座標，並引導使用者輸入新的座標設定。
    """
    print("\n" + "=" * 55)
    print("  滑鼠座標測量與設定工具")
    print("=" * 55)
    print("  1. 程式會開始即時顯示滑鼠所在的 X, Y 座標。")
    print("  2. 請將滑鼠移動到目標位置後，記錄該座標值。")
    print("  3. 按 Ctrl+C 可以結束即時顯示，並開始設定新座標。")
    print("-" * 55)
    print("  需要設定的目標有：")
    print("    - [搜尋框] (預設約 155, 125)")
    print("    - [K線圖右鍵] (預設約 500, 200)")
    print("    - [匯出選單] (預設約 550, 475)")
    print("-" * 55)
    
    input("[->] 按 [Enter] 鍵開始顯示座標... (結束請按 Ctrl+C)")
    
    try:
        while True:
            x, y = pyautogui.position()
            print(f"\r  目前滑鼠座標：X={x:4d}, Y={y:4d}  (結束請按 Ctrl+C)", end="", flush=True)
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n\n  [已結束顯示] 開始座標輸入流程...")

    def prompt_coord(label, current_val):
        cx, cy = current_val
        print(f"\n⚙️  設定 [{label}] 座標:")
        try:
            val_x = input(f"   X 座標 (目前為 {cx}，按 Enter 保持原樣): ").strip()
            x = int(val_x) if val_x else cx
        except ValueError:
            print("   ⚠️ 輸入無效，保持原值")
            x = cx

        try:
            val_y = input(f"   Y 座標 (目前為 {cy}，按 Enter 保持原樣): ").strip()
            y = int(val_y) if val_y else cy
        except ValueError:
            print("   ⚠️ 輸入無效，保持原值")
            y = cy
        
        return (x, y)

    COORD["stock_search"] = prompt_coord("搜尋框 (Step1)", COORD["stock_search"])
    COORD["kline_right_click"] = prompt_coord("K線圖右鍵 (Step2)", COORD["kline_right_click"])
    COORD["export_menu"] = prompt_coord("匯出選單 (Step2)", COORD["export_menu"])

    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(COORD, f, indent=4)
        print(f"\n✅ 座標設定已成功存入設定檔：{CONFIG_FILE}")
    except Exception as e:
        print(f"\n❌ 儲存座標設定檔失敗: {e}")

    print("\n目前套用座標為：")
    for k, v in COORD.items():
        print(f"  {k:18s}: {v}")
    print("=" * 55 + "\n")
    input("[->] 按 [Enter] 鍵繼續執行 RPA 匯出程式...")


def update_stock_database(success_list):
    """
    將匯出成功的 CSV 轉為 Excel，移入 Stock original，並將舊的 Excel 移到備份資料夾。
    """
    stock_original_dir = os.path.join(STOCK_ANALYSIS_DIR, "Stock original")
    log('🗃️', "開始進行資料庫更新作業...")

    for item in success_list:
        parts = item.split()
        if len(parts) < 2:
            continue
        code, name = parts[0], parts[1]
        
        csv_name = f"{code}_{name}_{DATE_TODAY}.csv"
        csv_path = os.path.join(OUTPUT_FOLDER, csv_name)
        
        if not os.path.exists(csv_path):
            log('⚠️ ', f"找不到 CSV 檔案：{csv_path}，跳過")
            continue
            
        try:
            # 讀取今日 CSV
            df = pd.read_csv(csv_path, encoding='cp950')
            
            # 設定新 Excel 路徑
            new_xlsx_name = f"{code}_{name}_EOM_{DATE_TODAY}.xlsx"
            new_xlsx_path = os.path.join(stock_original_dir, new_xlsx_name)
            
            # 搜尋 Stock original 中的舊 Excel
            old_pattern = os.path.join(stock_original_dir, f"{code}_{name}_EOM_*.xlsx")
            old_files = glob.glob(old_pattern)
            
            # 備份舊檔案
            for old_file in old_files:
                if os.path.basename(old_file) == new_xlsx_name:
                    continue
                
                date_match = re.search(r'_EOM_(\d{8})\.xlsx', os.path.basename(old_file))
                old_date = date_match.group(1) if date_match else "old_files"
                
                backup_dir = os.path.join(stock_original_dir, old_date)
                os.makedirs(backup_dir, exist_ok=True)
                
                backup_path = os.path.join(backup_dir, os.path.basename(old_file))
                log('📦', f"正在備份舊檔案：{os.path.basename(old_file)} -> {old_date}/")
                try:
                    if os.path.exists(backup_path):
                         os.remove(backup_path)
                    shutil.move(old_file, backup_path)
                except Exception as ex:
                    log('⚠️ ', f"備份失敗：{ex}")
            
            # 將今日資料轉存為 Excel
            log('💾', f"正在轉換並寫入 Excel：{new_xlsx_name}")
            df.to_excel(new_xlsx_path, index=False, engine='openpyxl')
            log('✅', f"順利更新 {code} {name} 資料庫")
            
        except Exception as e:
            log('❌', f"更新個股 {code} {name} 時出錯：{e}")



# ================================================================
#  主程式
# ================================================================

def switch_to_default_desktop():
    import ctypes
    try:
        hwinsta = ctypes.windll.user32.OpenWindowStationA(b"WinSta0", False, 0x37F)
        if hwinsta:
            hdesk = ctypes.windll.user32.OpenDesktopA(b"Default", 0, False, 0x1FF)
            if hdesk:
                ret = ctypes.windll.user32.SetThreadDesktop(hdesk)
                return ret == 1
    except:
        pass
    return False

def main():
    switch_to_default_desktop()
    # 清空上次的 log
    try:
        log_path = os.path.join(SCRIPT_DIR, "stock_exporter.log")
        if os.path.exists(log_path):
            os.remove(log_path)
    except:
        pass

    # 載入與詢問更新座標
    print("=" * 62, flush=True)
    print("  座標校準確認", flush=True)
    print("=" * 62, flush=True)
    print("  目前套用座標：")
    for k, v in COORD.items():
        print(f"    {k:18s}: {v}", flush=True)
    print("-" * 62, flush=True)
    
    ans = input("[?] 是否需要更新/校準滑鼠座標設定？(y/N) [預設為 N]: ").strip().lower()
    if ans == 'y':
        calibrate_coordinates()

    # 詢問起始個股代號
    print("-" * 62, flush=True)
    start_code = input("[?] 請輸入起始個股代號 (按 Enter 則從第一筆開始): ").strip()
    
    global STOCK_LIST
    if start_code:
        found_idx = -1
        for idx, stock in enumerate(STOCK_LIST):
            if stock["code"] == start_code:
                found_idx = idx
                break
        
        if found_idx != -1:
            STOCK_LIST = STOCK_LIST[found_idx:]
            print(f"✅ 設定成功！將從第 {found_idx+1} 筆個股 {start_code} 開始往後執行。", flush=True)
        else:
            print(f"⚠️ 找不到個股代號 {start_code}，將依預設從第一筆開始執行。", flush=True)

    print("\n" + "=" * 62, flush=True)
    print("  台新贏家快手 V5.1.1  RPA 精確座標版 v2", flush=True)
    print("=" * 62, flush=True)
    print(f"  座標：搜尋框{COORD['stock_search']} / 右鍵{COORD['kline_right_click']} / 選單{COORD['export_menu']}", flush=True)
    print(f"  輸出：{OUTPUT_FOLDER}", flush=True)
    print(f"  日期：{DATE_TODAY}", flush=True)
    print(f"  個股：{len(STOCK_LIST)} 支", flush=True)
    print(flush=True)


    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    # ── 倒數讓使用者切換視窗 ──
    print("⚠️  請確認台新贏家快手已開啟並顯示 K 線圖！", flush=True)
    print("   滑鼠移至左上角可緊急中止。", flush=True)
    print(flush=True)
    for i in range(5, 0, -1):
        print(f"  倒數 {i} 秒...", flush=True)
        time.sleep(1)
    
    # 強制尋找並聚焦贏家快手
    hwnd = find_winner_hwnd()
    if not hwnd:
        print("❌ 找不到台新贏家快手，請確認軟體已開啟！")
        return
    focus_winner_safely(hwnd)
    time.sleep(1.0)
    
    print("🚀 開始！\n", flush=True)

    success, failed = [], []
    total = len(STOCK_LIST)

    for idx, stock in enumerate(STOCK_LIST, start=1):
        code, name = stock["code"], stock["name"]

        print(f"\n{'─'*55}", flush=True)
        print(f"  [{idx:2d}/{total}]  {code}  {name}", flush=True)
        print(f"{'─'*55}", flush=True)

        try:
            step1_input_stock(code, name)
            before_ts = step2_export_excel()
            ok = step3_switch_and_clean_com(before_ts, code, name)

            if ok:
                success.append(f"{code} {name}")
            else:
                failed.append(f"{code} {name}")

        except pyautogui.FailSafeException:
            print("\n🛑 緊急中止（滑鼠移至左上角）", flush=True)
            break
        except Exception as e:
            import traceback
            log('❌', f"例外：{e}")
            traceback.print_exc()
            failed.append(f"{code} {name}")
            # 例外恢復
            try:
                pyautogui.press('escape')
                time.sleep(0.3)
                pyautogui.hotkey('alt', 'f4')
                time.sleep(0.5)
                pyautogui.press('n')
                time.sleep(1.0)
            except Exception:
                pass

        # 最後一支不切換
        if idx < total:
            step5_back_to_winner()
            time.sleep(WAIT["between_stocks"])

    # ── 結果報告 ──
    print(f"\n{'='*62}", flush=True)
    print(f"  完成！成功 {len(success)} 支 / 失敗 {len(failed)} 支", flush=True)
    for s in success:
        print(f"  ✅ {s}", flush=True)
    for f in failed:
        print(f"  ❌ {f}（請手動補匯）", flush=True)
    print(f"  📁 {OUTPUT_FOLDER}", flush=True)
    print(f"{'='*62}", flush=True)

    # ── Excel 資料庫自動更新與舊檔備份 ──
    if len(success) > 0:
        print(f"\n{'='*62}", flush=True)
        print("  資料庫自動更新 (CSV 轉存 Excel 並備份舊資料)", flush=True)
        print("=" * 62, flush=True)
        ans = input("[?] 是否將今日匯出的 CSV 檔案轉換為 Excel 並更新至 Stock original 目錄？(Y/n) [預設為 Y]: ").strip().lower()
        if ans != 'n':
            update_stock_database(success)
        print("=" * 62, flush=True)



if __name__ == "__main__":
    main()
