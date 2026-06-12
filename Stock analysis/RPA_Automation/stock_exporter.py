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

OUTPUT_FOLDER = r"E:\G-AI-1\Stock analysis\Stock original\auto_export"
DATE_TODAY    = datetime.now().strftime("%Y%m%d")

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
        with open(r"E:\G-AI-1\Stock analysis\RPA_Automation\stock_exporter.log", "a", encoding="utf-8") as f:
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


def step3_switch_and_clean(before_ts, code, name):
    """
    Step3：切換至 Excel 視窗 → 搜尋暫存檔 → 清洗箭頭符號
    """
    log('📌 STEP3', "切換 Excel + 執行清洗")

    # 找到並切換至 Excel
    excel_win = find_excel_window(timeout=8.0)
    activate_win(excel_win, "Excel")

    # 搜尋匯出的暫存 Excel
    raw_path = find_latest_excel_after(before_ts)
    if not raw_path:
        log('❌', "找不到匯出的 Excel 暫存檔！請確認軟體匯出路徑")
        return None, None

    log('📄', f"找到暫存檔：{os.path.basename(raw_path)}")

    # 讀取並清洗
    try:
        if raw_path.lower().endswith('.txt'):
            df = pd.read_csv(raw_path, sep='\t', encoding='cp950')
        else:
            df = pd.read_excel(raw_path, sheet_name=0, header=0, engine='openpyxl')
        log('📊', f"讀取完成：{len(df)} 筆 × {len(df.columns)} 欄")
    except Exception as e:
        log('❌', f"讀取失敗：{e}")
        return None, raw_path

    cleaned_count = 0
    for col in df.columns:
        if df[col].dtype == object:
            cs = df[col].apply(clean_value)
            if cs.notna().mean() > 0.3:
                df[col] = cs
                cleaned_count += 1

    log('✅', f"清洗完成，處理 {cleaned_count} 個欄位（已轉 float）")
    return df, raw_path


def step4_save_and_close(df, raw_path, code, name):
    """
    Step4：儲存清洗後的 Excel → 關閉 Excel（不儲存原始暫存檔）
    """
    log('📌 STEP4', "儲存 + 關閉 Excel")

    out_path = None

    # ── 儲存 ──
    if df is not None:
        filename  = f"{code}_{name}_{DATE_TODAY}.xlsx"
        out_path  = os.path.join(OUTPUT_FOLDER, filename)
        try:
            df.to_excel(out_path, index=False, engine='openpyxl')
            log('✅', f"儲存成功：{filename}")
        except Exception as e:
            log('❌', f"儲存失敗：{e}")
            out_path = None

    # ── 關閉 Excel ──
    excel_win = find_excel_window(timeout=2.0)
    if excel_win:
        activate_win(excel_win, "Excel")
        time.sleep(0.2)

    log('🖱 ', "送出 Alt+F4 關閉 Excel")
    pyautogui.hotkey('alt', 'f4')
    time.sleep(0.8)

    # 若出現「是否儲存？」→ 按 N 不儲存（已另存至 output_folder）
    log('⌨️ ', "按 N 不儲存原始暫存檔")
    pyautogui.press('n')
    time.sleep(WAIT["excel_close"])

    log('✅', "Step4 完成")
    return out_path


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
        if os.path.exists(r"E:\G-AI-1\Stock analysis\RPA_Automation\stock_exporter.log"):
            os.remove(r"E:\G-AI-1\Stock analysis\RPA_Automation\stock_exporter.log")
    except:
        pass
    print("=" * 62, flush=True)
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
            df, raw_path = step3_switch_and_clean(before_ts, code, name)
            out_path = step4_save_and_close(df, raw_path, code, name)

            if out_path:
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


if __name__ == "__main__":
    main()
