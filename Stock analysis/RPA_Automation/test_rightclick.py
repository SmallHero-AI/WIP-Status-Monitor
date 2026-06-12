# -*- coding: utf-8 -*-
"""
等待台新贏家快手開啟後，自動執行 Step1→Step2 並截圖右鍵選單
工作管理員名稱：HTS Kway Corporation
"""
import pyautogui, win32gui, win32con, win32api, time, sys, os, ctypes
from datetime import datetime

# Redirect output to log file
sys.stdout = open(r"E:\G-AI-1\Stock analysis\RPA_Automation\test_rightclick.log", "w", encoding="utf-8")
sys.stderr = sys.stdout

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

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

KEYWORDS = ['贏家', 'HTS', 'Kway', 'kway', 'Winner', '快手', '台新']

def find_winner_hwnd():
    """搜尋台新贏家快手（含 HTS Kway Corporation）"""
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
        if r - l > 400:
            return h, t
    return result[0]

def force_restore(hwnd):
    """用 WM_SYSCOMMAND 強制還原（對 HTS 軟體有效）"""
    for sw in [win32con.SW_RESTORE, win32con.SW_SHOWNORMAL]:
        win32gui.ShowWindow(hwnd, sw)
        time.sleep(0.4)
        l, t, r, b = win32gui.GetWindowRect(hwnd)
        if l > -1000 and r - l > 400:
            try: win32gui.SetForegroundWindow(hwnd)
            except: pass
            return True
    win32api.PostMessage(hwnd, win32con.WM_SYSCOMMAND, win32con.SC_RESTORE, 0)
    time.sleep(0.8)
    l, t, r, b = win32gui.GetWindowRect(hwnd)
    if l > -1000 and r - l > 400:
        try: win32gui.SetForegroundWindow(hwnd)
        except: pass
        return True
    return False

log("=== 等待台新贏家快手開啟 ===")
log(f"搜尋關鍵字：{KEYWORDS}")
hwnd, title = find_winner_hwnd()
if not hwnd:
    log("❌ 找不到台新贏家快手，請確認已開啟")
    sys.exit(1)

log(f"✅ 找到！hwnd={hwnd}，標題：{title}")

# ── 確認視窗位置 ──
l, t, r, b = win32gui.GetWindowRect(hwnd)
log(f"視窗位置：({l},{t}) 大小：{r-l}x{b-t}")

# ── 還原視窗 ──
if l < -100 or r - l < 400:
    log("視窗在螢幕外，嘗試還原...")
    ok = force_restore(hwnd)
    log(f"還原結果：{'✅ 成功' if ok else '❌ 失敗，請手動點擊工作列圖示'}")
    time.sleep(0.8)
    l, t, r, b = win32gui.GetWindowRect(hwnd)
    log(f"還原後位置：({l},{t}) 大小：{r-l}x{b-t}")
else:
    log("視窗已在螢幕上，直接使用")
    try: win32gui.SetForegroundWindow(hwnd)
    except: pass
    time.sleep(0.5)

# ── 3 秒倒數，執行 Step1 ──
l, t, r, b = win32gui.GetWindowRect(hwnd)
if r - l > 400 and l > -100:
    log("\n視窗已就緒！3 秒後執行 Step1（輸入 2330）...")
    time.sleep(3)

    log("▶ Step1：移動到 (155,125) 點擊搜尋框")
    pyautogui.FAILSAFE = False
    pyautogui.moveTo(155, 125, duration=0.6)
    time.sleep(0.2)
    pyautogui.click()
    time.sleep(0.3)
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.15)
    log("▶ 輸入 2330...")
    pyautogui.typewrite('2330', interval=0.15)
    time.sleep(0.2)
    pyautogui.press('enter')
    log("▶ 等待 K 線刷新 2.5 秒...")
    time.sleep(2.5)
    log("✅ Step1 完成！")

    log("\n▶ Step2：右鍵 (500,200)...")
    pyautogui.moveTo(500, 200, duration=0.6)
    time.sleep(0.2)
    pyautogui.rightClick()
    time.sleep(1.5)  # 讓選單完全展開

    # 截圖保存（含選單畫面）
    shot = pyautogui.screenshot()
    shot_path = r"E:\G-AI-1\Stock analysis\RPA_Automation\right_click_menu.png"
    shot.save(shot_path)
    log(f"📸 截圖已儲存：{shot_path}")
    log("請查看截圖，確認 (550,475) 是否對應「匯出至 Excel」")

    time.sleep(3)
    pyautogui.press('escape')
    log("ESC 關閉選單，測試完成")
else:
    log(f"⚠️ 視窗大小異常 {r-l}x{b-t}，無法繼續")
    log("請手動將台新贏家快手最大化後，重新執行此腳本")
