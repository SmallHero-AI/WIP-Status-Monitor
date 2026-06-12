# -*- coding: utf-8 -*-
import pyautogui
import win32api, win32con, win32process, win32gui
import time
import os
import ctypes
import sys

# Redirect output to file
sys.stdout = open(r"E:\G-AI-1\Stock analysis\RPA_Automation\test_mouse.log", "w", encoding="utf-8")
sys.stderr = sys.stdout

def get_session_id():
    try:
        pid = os.getpid()
        session_id = ctypes.c_ulong()
        if ctypes.windll.kernel32.ProcessIdToSessionId(pid, ctypes.byref(session_id)):
            return session_id.value
        return "Unknown"
    except Exception as e:
        return f"Error: {e}"

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

print("Current Session ID:", get_session_id())
print("Is Admin (IsUserAnAdmin):", is_admin())
print("Current Mouse Position:", pyautogui.position())

# Switch to default desktop
try:
    hwinsta = ctypes.windll.user32.OpenWindowStationA(b"WinSta0", False, 0x37F)
    if hwinsta:
        hdesk = ctypes.windll.user32.OpenDesktopA(b"Default", 0, False, 0x1FF)
        if hdesk:
            ret = ctypes.windll.user32.SetThreadDesktop(hdesk)
            print("SetThreadDesktop ret:", ret)
except Exception as e:
    print("Desktop switch error:", e)

# Disable fail-safe just for this test
pyautogui.FAILSAFE = False

# Try moving mouse with pyautogui to (300, 300)
try:
    print("Moving with pyautogui to (300, 300)...")
    pyautogui.moveTo(300, 300, duration=1.0)
    print("New Mouse Position (pyautogui):", pyautogui.position())
except Exception as e:
    print("pyautogui error:", e)

# Try moving mouse with win32api to (500, 500)
try:
    print("Moving with win32api to (500, 500)...")
    win32api.SetCursorPos((500, 500))
    time.sleep(0.5)
    print("New Mouse Position (win32api):", pyautogui.position())
except Exception as e:
    print("win32api error:", e)
