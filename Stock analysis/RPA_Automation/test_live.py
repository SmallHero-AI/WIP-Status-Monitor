# -*- coding: utf-8 -*-
"""
台新贏家快手 RPA - 完整流程（修正視窗聚焦 + 搜尋正確 Excel 路徑）

修正重點：
  1. SetForegroundWindow 後，額外用 pyautogui.click 點擊視窗本身，確保焦點
  2. 加入更廣的 Excel 暫存路徑搜尋（包含 HTS 可能的輸出目錄）
  3. 右鍵前先確認滑鼠在視窗範圍內
"""
import pyautogui
import win32gui, win32con, win32api
import time, sys, os, re, glob, ctypes
import pandas as pd
from datetime import datetime
import win32com.client

# Redirect output to file
sys.stdout = open(r"E:\G-AI-1\Stock analysis\RPA_Automation\test_live.log", "w", encoding="utf-8")
sys.stderr = sys.stdout

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def switch_to_default_desktop():
    try:
        hwinsta = ctypes.windll.user32.OpenWindowStationA(b"WinSta0", False, 0x37F)
        if hwinsta:
            hdesk = ctypes.windll.user32.OpenDesktopA(b"Default", 0, False, 0x1FF)
            if hdesk:
                ret = ctypes.windll.user32.SetThreadDesktop(hdesk)
                log(f"SetThreadDesktop ret: {ret}")
                return ret == 1
    except Exception as e:
        log(f"switch_to_default_desktop error: {e}")
    return False

# Ensure we are on Default desktop
switch_to_default_desktop()

pyautogui.FAILSAFE = False
MOUSE_DURATION = 0.5

# ────────────────────────────────────────────
# 搜尋 HTS 視窗
# ────────────────────────────────────────────
def find_winner_hwnd():
    KEYWORDS = ['贏家', 'HTS', 'Kway', 'Winner', '快手', '台新']
    result = []
    def cb(h, _):
        try:
            t = win32gui.GetWindowText(h)
            if not t.strip(): return
            for kw in KEYWORDS:
                if kw in t:
                    result.append((h, t))
                    return
        except: pass
    win32gui.EnumWindows(cb, None)
    if not result: return None, None
    for h, t in result:
        l, top, r, b = win32gui.GetWindowRect(h)
        if r - l > 400: return h, t
    return result[0]

# ────────────────────────────────────────────
# 強制把 HTS 視窗帶到前景並給予焦點
# ────────────────────────────────────────────
def focus_winner(hwnd):
    """
    安全聚焦視窗：如果已在螢幕上，僅進行 SetForegroundWindow，絕不還原或移動視窗。
    只有在最小化或在螢幕外時才進行還原。
    """
    log("安全聚焦台新贏家快手...")
    try:
        is_min = win32gui.IsIconic(hwnd)
        l, top, r, b = win32gui.GetWindowRect(hwnd)
        if is_min or l < -100 or r - l < 400:
            log("  偵測到最小化或在螢幕外，執行還原...")
            win32api.PostMessage(hwnd, win32con.WM_SYSCOMMAND, win32con.SC_RESTORE, 0)
            time.sleep(0.8)
            l, top, r, b = win32gui.GetWindowRect(hwnd)
        
        try:
            win32gui.SetForegroundWindow(hwnd)
        except Exception as e:
            log(f"  SetForegroundWindow: {e}")
        time.sleep(0.4)
        
        # 在標題列點一下確認焦點 (不移動/縮放視窗)
        win_cx = (l + r) // 2
        win_title_y = top + 10
        log(f"  視窗範圍: ({l},{top}) ~ ({r},{b})")
        log(f"  在標題列 ({win_cx}, {win_title_y}) 點一下確認焦點")
        pyautogui.moveTo(win_cx, win_title_y, duration=0.4)
        time.sleep(0.1)
        pyautogui.click()
        time.sleep(0.5)
        log("✅ 視窗已聚焦")
    except Exception as e:
        log(f"❌ 聚焦失敗: {e}")

# ────────────────────────────────────────────
# 搜尋所有可能的 Excel 匯出路徑
# ────────────────────────────────────────────
def find_latest_excel(before_ts):
    """搜尋 before_ts 之後新增的所有 xlsx/xls 檔案"""
    import subprocess
    try:
        r = subprocess.run(['wmic', 'process', 'where', "name like '%HTS%'",
                            'get', 'ExecutablePath'],
                           capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=5)
        for line in r.stdout.splitlines():
            line = line.strip()
            if line and 'ExecutablePath' not in line:
                hts_dir = os.path.dirname(line)
                log(f"  HTS 安裝路徑: {hts_dir}")
    except Exception:
        pass

    SEARCH_DIRS = [
        r"C:\ML_Speed\user",
        os.path.expanduser("~/Desktop"),
        os.path.expanduser("~/Documents"),
        os.path.expanduser("~/Downloads"),
        r"C:\Users\loadmin\Desktop",
        r"C:\Users\loadmin\Documents",
        r"C:\Users\loadmin\Downloads",
        os.environ.get("TEMP", ""),
        os.path.join(os.environ.get("LOCALAPPDATA",""), "Temp"),
        r"C:",  # 根目錄快速搜一層（不含子目錄）
    ]

    newest, newest_ts = None, before_ts
    for d in SEARCH_DIRS:
        if not d or not os.path.exists(d):
            continue
        for ext in ["*.xlsx", "*.xls", "*.txt"]:
            for f in glob.glob(os.path.join(d, ext)):
                try:
                    mt = os.path.getmtime(f)
                    if mt > newest_ts:
                        newest_ts = mt
                        newest    = f
                except OSError:
                    pass

    return newest

# ────────────────────────────────────────────
# 主流程
# ────────────────────────────────────────────
log("=== 台新贏家快手 RPA（修正版）===")

# 找視窗
hwnd, title = find_winner_hwnd()
if not hwnd:
    log("❌ 找不到台新贏家快手，請確認軟體已開啟")
    sys.exit(1)
log(f"✅ 找到: {repr(title)}  hwnd={hwnd}")

# 聚焦（三步驟）
focus_winner(hwnd)
time.sleep(0.8)

# ── Step1：輸入股號 ──
log("\n=== Step1：輸入 2330 ===")
log("移動到搜尋框 (155, 125)...")
pyautogui.moveTo(155, 125, duration=MOUSE_DURATION)
time.sleep(0.2)
pyautogui.click()
time.sleep(0.4)
pyautogui.hotkey('ctrl', 'a')
time.sleep(0.15)
log("輸入 2330...")
pyautogui.typewrite('2330', interval=0.15)
time.sleep(0.2)
pyautogui.press('enter')
log("等待 K 線刷新 2.5 秒...")
time.sleep(2.5)
log("✅ Step1 完成")

# ── Step2：右鍵匯出 ──
log("\n=== Step2：右鍵 K 線圖 ===")
before_ts = time.time()

log("移動到 (500, 200) 右鍵...")
pyautogui.moveTo(500, 200, duration=MOUSE_DURATION)
time.sleep(0.3)
pyautogui.rightClick()
time.sleep(1.5)  # 等選單完全展開

# 截圖（含選單）
shot_path = r"E:\G-AI-1\Stock analysis\RPA_Automation\right_click_menu.png"
pyautogui.screenshot().save(shot_path)
log(f"📸 截圖儲存：{shot_path}")

log("移動到 (550, 475) 點擊匯出...")
pyautogui.moveTo(550, 475, duration=MOUSE_DURATION)
time.sleep(0.3)
pyautogui.click()
log("等待 Excel 開啟 6 秒...")
time.sleep(6.0)

# 再截圖確認目前畫面
shot2_path = r"E:\G-AI-1\Stock analysis\RPA_Automation\after_export.png"
pyautogui.screenshot().save(shot2_path)
log(f"📸 匯出後截圖：{shot2_path}")
log("✅ Step2 完成")

# ── Step3 & Step4：使用 Excel COM 自動化清洗與另存為 CSV ──
log("\n=== Step3 & Step4：Excel COM 自動化取代與存為 CSV ===")

import pygetwindow as gw
excel_wins = [w for w in gw.getAllWindows() if 'Excel' in w.title or '.xlsx' in w.title or '.txt' in w.title]
if excel_wins:
    try:
        excel_wins[0].activate()
        time.sleep(1.0)
    except Exception as e:
        log(f"激活 Excel 視窗失敗: {e}")

# 獲取 Excel COM 物件
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
    log("❌ 無法取得作用中的 Excel 應用程式實例 (COM)")
    sys.exit(1)

try:
    excel_app.DisplayAlerts = False
    
    # 尋找對應的活頁簿 (2330)
    wb = None
    for w in excel_app.Workbooks:
        if "2330" in w.Name:
            wb = w
            break
    if not wb:
        log("⚠️ 找不到名稱含有 2330 的活頁簿，使用 ActiveWorkbook")
        wb = excel_app.ActiveWorkbook

    if not wb:
        log("❌ 無法取得 Excel 活頁簿！")
        sys.exit(1)

    log(f"📄 已取得活頁簿：{wb.Name}")
    ws = wb.ActiveSheet

    # 執行取代
    log("🧹 在 Excel 執行取代：將 ↑ 取代為空白")
    ws.Cells.Replace(What="↑", Replacement="", LookAt=2, SearchOrder=1, MatchCase=False)
    log("🧹 在 Excel 執行取代：將 ↓ 取代為空白")
    ws.Cells.Replace(What="↓", Replacement="", LookAt=2, SearchOrder=1, MatchCase=False)

    # 儲存為 CSV
    out_dir = r"E:\G-AI-1\Stock analysis\Stock original\auto_export"
    os.makedirs(out_dir, exist_ok=True)
    csv_name = f"2330_台積電_{datetime.now().strftime('%Y%m%d')}.csv"
    csv_path = os.path.join(out_dir, csv_name)

    if os.path.exists(csv_path):
        try:
            os.remove(csv_path)
        except Exception:
            pass

    log(f"💾 另存為 CSV 格式：{csv_path}")
    wb.SaveAs(Filename=csv_path, FileFormat=6)

    # 關閉活頁簿
    wb.Close(SaveChanges=False)
    log("✅ 已成功儲存並關閉活頁簿")

    # 若無其他活頁簿，關閉整個 Excel 應用程式
    if excel_app.Workbooks.Count == 0:
        excel_app.Quit()
        log("✅ Excel 應用程式已關閉")

except Exception as e:
    log(f"❌ Excel COM 處理失敗：{e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    try:
        if excel_app:
            excel_app.DisplayAlerts = True
    except:
        pass

log("\n=== 完成 ===")
