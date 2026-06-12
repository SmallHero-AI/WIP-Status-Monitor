# -*- coding: utf-8 -*-
import ctypes
import win32api, win32process, win32gui, win32con
import pyautogui
import time
import sys

# Redirect output to file
sys.stdout = open(r"E:\G-AI-1\Stock analysis\RPA_Automation\admin_test.log", "w", encoding="utf-8")
sys.stderr = sys.stdout

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

def switch_to_default_desktop():
    try:
        hwinsta = ctypes.windll.user32.OpenWindowStationA(b"WinSta0", False, 0x37F)
        if hwinsta:
            hdesk = ctypes.windll.user32.OpenDesktopA(b"Default", 0, False, 0x1FF)
            if hdesk:
                ret = ctypes.windll.user32.SetThreadDesktop(hdesk)
                log(f"SetThreadDesktop: {ret}")
                return ret == 1
    except Exception as e:
        log(f"switch_to_default_desktop error: {e}")
    return False

log("Admin test started")
switch_to_default_desktop()

# Find HTS
hwnd = 15142340 # We can also search dynamically
log(f"Target hwnd: {hwnd}")

# Restore window
win32api.PostMessage(hwnd, win32con.WM_SYSCOMMAND, win32con.SC_RESTORE, 0)
time.sleep(1.0)

# Bring to front
try:
    win32gui.SetForegroundWindow(hwnd)
    log("SetForegroundWindow called")
except Exception as e:
    log(f"SetForegroundWindow error: {e}")
time.sleep(0.5)

# Move mouse and click to focus
l, top, r, b = win32gui.GetWindowRect(hwnd)
win_cx = (l + r) // 2
win_title_y = top + 10
log(f"Window rect: {l}, {top}, {r}, {b}")
log(f"Moving mouse to title bar ({win_cx}, {win_title_y})")

pyautogui.FAILSAFE = False
pyautogui.moveTo(win_cx, win_title_y, duration=0.5)
pyautogui.click()
time.sleep(0.5)

# Take screenshot 1
pyautogui.screenshot().save(r"E:\G-AI-1\Stock analysis\RPA_Automation\admin_test_1.png")
log("Saved screenshot 1")

# Move to search box
log("Moving to (155, 125)")
pyautogui.moveTo(155, 125, duration=0.5)
pyautogui.click()
time.sleep(0.5)

# Take screenshot 2
pyautogui.screenshot().save(r"E:\G-AI-1\Stock analysis\RPA_Automation\admin_test_2.png")
log("Saved screenshot 2")

log("Admin test finished")
