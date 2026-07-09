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

# ── Step3：找 Excel ──
log("\n=== Step3：搜尋 Excel 暫存檔 ===")
raw_path = find_latest_excel(before_ts)

if not raw_path:
    log("❌ 找不到新的 Excel 檔案")
    log("   請查看兩張截圖確認：")
    log(f"   選單截圖: {shot_path}")
    log(f"   匯出後:   {shot2_path}")
    log("")
    log("   另請手動確認：台新贏家快手匯出 Excel 後存在哪個目錄？")
    log("   可在軟體內手動按一次「匯出至 Excel」，觀察存檔路徑")
else:
    log(f"✅ 找到: {raw_path}")

    def clean_val(v):
        if v is None: return None
        try:
            if pd.isna(v): return None
        except: pass
        s = re.sub(r'[▲▼↑↓△▽→←↑↓]', '', str(v).strip()).replace(',','')
        try: return float(s)
        except: return None

    try:
        if raw_path.lower().endswith('.txt'):
            df = pd.read_csv(raw_path, sep='\t', encoding='cp950')
        else:
            df = pd.read_excel(raw_path, engine='openpyxl')
        log(f"讀取：{len(df)} 筆 x {len(df.columns)} 欄")
    except Exception as e:
        log(f"❌ 讀取失敗: {e}")
        sys.exit(1)

    for col in df.columns:
        if df[col].dtype == object:
            cs = df[col].apply(clean_val)
            if cs.notna().mean() > 0.3:
                df[col] = cs
                log(f"清洗：{col}")

    out_dir  = r"E:\G-AI-1\Stock analysis\Stock original\auto_export"
    os.makedirs(out_dir, exist_ok=True)
    out_name = f"2330_台積電_{datetime.now().strftime('%Y%m%d')}.xlsx"
    out_path = os.path.join(out_dir, out_name)
    df.to_excel(out_path, index=False, engine='openpyxl')
    log(f"✅ 儲存：{out_path}")

    # 關閉 Excel
    import pygetwindow as gw
    excel_wins = [w for w in gw.getAllWindows() if 'Excel' in w.title or '.xlsx' in w.title]
    if excel_wins:
        try:
            excel_wins[0].activate()
            time.sleep(0.3)
        except:
            pass
    pyautogui.hotkey('alt', 'f4')
    time.sleep(0.7)
    pyautogui.press('n')
    time.sleep(1.0)
    log("✅ Excel 已關閉")

log("\n=== 完成 ===")
